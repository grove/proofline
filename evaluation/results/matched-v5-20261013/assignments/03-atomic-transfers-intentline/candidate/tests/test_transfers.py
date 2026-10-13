import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Transfers(unittest.TestCase):
    def assert_rejected_without_mutation(self, payload):
        for function in (app.process, service.handle):
            with self.subTest(function=function.__name__, payload=payload):
                snapshot = copy.deepcopy(payload)
                with self.assertRaises(ValueError):
                    function(payload)
                self.assertEqual(payload, snapshot)

    def test_ordered_transfers_and_interface_parity(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 1},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 4]],
            "extra": {"nested": [1, 2]},
        }
        snapshot = copy.deepcopy(payload)
        expected = {"balances": {"a": 4, "b": 2, "c": 0}}
        for function in (app.process, service.handle):
            with self.subTest(function=function.__name__):
                result = function(payload)
                self.assertEqual(result, expected)
                self.assertEqual(payload, snapshot)
                self.assertIsNot(result["balances"], payload["balances"])
                result["balances"]["a"] = 999
                self.assertEqual(payload, snapshot)

    def test_empty_accounts_and_transfers(self):
        self.assertEqual(app.process({"balances": {}, "transfers": []}),
                         {"balances": {}})
        self.assertEqual(app.process({"balances": {"a": 0}, "transfers": []}),
                         {"balances": {"a": 0}})

    def test_zero_exact_balance_and_self_transfers(self):
        cases = [
            ({"a": 0, "b": 0}, [["a", "b", 0]], {"a": 0, "b": 0}),
            ({"a": 5, "b": 0}, [["a", "b", 5]], {"a": 0, "b": 5}),
            ({"a": 5}, [["a", "a", 0], ["a", "a", 5]], {"a": 5}),
            ({"a": 0}, [["a", "a", 0]], {"a": 0}),
        ]
        for balances, transfers, expected in cases:
            with self.subTest(balances=balances, transfers=transfers):
                self.assertEqual(app.process({"balances": balances, "transfers": transfers}),
                                 {"balances": expected})

    def test_names_are_nonempty_without_trimming(self):
        payload = {"balances": {" ": 3, "\t": 0, "账户": 1},
                   "transfers": [[" ", "\t", 2], ["账户", " ", 1]]}
        self.assertEqual(app.process(payload),
                         {"balances": {" ": 2, "\t": 2, "账户": 0}})

    def test_arbitrary_size_integers(self):
        amount = 10 ** 100
        self.assertEqual(app.process({"balances": {"a": amount, "b": 0},
                                      "transfers": [["a", "b", amount]]}),
                         {"balances": {"a": 0, "b": amount}})

    def test_intermediate_overdraft_cannot_be_offset_later(self):
        self.assert_rejected_without_mutation({
            "balances": {"a": 1, "b": 5},
            "transfers": [["a", "b", 2], ["b", "a", 2]],
        })

    def test_oversized_self_transfer_rejects(self):
        self.assert_rejected_without_mutation({
            "balances": {"a": 5}, "transfers": [["a", "a", 6]],
        })

    def test_late_failures_preserve_all_input(self):
        for last_transfer in (["b", "a", 4], ["b", "missing", 0], ["b", "a", True]):
            self.assert_rejected_without_mutation({
                "balances": {"a": 5, "b": 0},
                "transfers": [["a", "b", 3], last_transfer],
                "extra": {"nested": [1, 2]},
            })

    def test_invalid_payload_shapes(self):
        cases = [None, False, 3, "payload", [], (), {},
                 {"balances": {}}, {"transfers": []},
                 {"balances": [], "transfers": []},
                 {"balances": None, "transfers": []}]
        for transfers in (None, {}, (), "", 0, True):
            cases.append({"balances": {"a": 5}, "transfers": transfers})
        for payload in cases:
            self.assert_rejected_without_mutation(payload)

    def test_invalid_balances_and_names(self):
        for balance in (True, False, -1, 1.0, "1", None, [], {}, float("inf")):
            self.assert_rejected_without_mutation({
                "balances": {"a": balance}, "transfers": [],
            })
        for name in ("", 1, False, None, ("a",)):
            self.assert_rejected_without_mutation({
                "balances": {name: 1}, "transfers": [],
            })

    def test_invalid_transfer_shapes_names_and_amounts(self):
        entries = [None, {}, "abc", 3, True, (), ("a", "b", 1), [],
                   ["a"], ["a", "b"], ["a", "b", 1, 2]]
        for name in ("", 1, True, None, [], {}, "missing"):
            entries.extend([[name, "b", 0], ["a", name, 0]])
        for amount in (True, False, -1, 1.0, "1", None, [], {}, float("inf")):
            entries.append(["a", "b", amount])
        for entry in entries:
            self.assert_rejected_without_mutation({
                "balances": {"a": 5, "b": 0}, "transfers": [entry],
            })


class Batch(unittest.TestCase):
    def test_empty_and_ordered_independent_results(self):
        self.assertEqual(service.batch([]), [])
        payloads = [
            {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
            {"balances": {"a": 7}, "transfers": [["a", "a", 7]]},
        ]
        snapshot = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [
            {"balances": {"a": 2, "b": 3}}, {"balances": {"a": 7}},
        ])
        self.assertEqual(payloads, snapshot)

    def test_non_list_rejected(self):
        for payloads in (None, {}, (), "", 1, True):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_members_reject_without_mutation(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        for invalid in (None, {}, [], {"balances": {"a": 0},
                                      "transfers": [["a", "a", 1]]}):
            for payloads in ([invalid, valid], [valid, invalid]):
                with self.subTest(payloads=payloads):
                    snapshot = copy.deepcopy(payloads)
                    with self.assertRaises(ValueError):
                        service.batch(payloads)
                    self.assertEqual(payloads, snapshot)

    def test_repeated_payloads_do_not_share_result_balances(self):
        payload = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        results = service.batch([payload, payload])
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}}] * 2)
        results[0]["balances"]["a"] = 99
        self.assertEqual(results[1], {"balances": {"a": 2, "b": 3}})
        self.assertEqual(payload["balances"], {"a": 5, "b": 0})


class CLI(unittest.TestCase):
    def run_cli(self, text="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=text, capture_output=True,
                              text=True, timeout=5)

    def test_json_success(self):
        result = self.run_cli(json.dumps({
            "balances": {"账户": 5, "b": 0},
            "transfers": [["账户", "b", 3]], "ignored": [1, 2],
        }))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"balances": {"账户": 2, "b": 3}})

    def test_invalid_input_has_no_partial_stdout(self):
        for text in ("{", "null", json.dumps({
                "balances": {"a": 5, "b": 0},
                "transfers": [["a", "b", 3], ["a", "b", 3]],
        }), json.dumps({"balances": {"a": True}, "transfers": []})):
            with self.subTest(text=text):
                result = self.run_cli(text)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_preserved(self):
        for args in (("--bogus",), ("--version", "extra"), ("extra",)):
            with self.subTest(args=args):
                result = self.run_cli("invalid json", args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

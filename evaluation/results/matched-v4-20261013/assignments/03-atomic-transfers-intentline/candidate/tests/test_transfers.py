import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
import service


class Transfers(unittest.TestCase):
    def assert_rejected_unchanged(self, payload):
        for entry in (process, service.handle):
            with self.subTest(entry=entry.__name__, payload=payload):
                before = copy.deepcopy(payload)
                with self.assertRaises(ValueError):
                    entry(payload)
                self.assertEqual(payload, before)

    def test_ordered_transfers_and_input_preservation(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 0},
            "transfers": [["a", "b", 3], ["b", "c", 2], ["c", "a", 1]],
            "extra": {"nested": [1, 2]},
        }
        before = copy.deepcopy(payload)
        for entry in (process, service.handle):
            result = entry(payload)
            self.assertEqual(result, {"balances": {"a": 3, "b": 1, "c": 1}})
            self.assertEqual(payload, before)
            result["balances"]["a"] = 999
            self.assertEqual(payload, before)

    def test_later_deposit_cannot_rescue_intermediate_overdraft(self):
        self.assert_rejected_unchanged({
            "balances": {"a": 5, "b": 0},
            "transfers": [["b", "a", 1], ["a", "b", 1]],
        })

    def test_rejection_after_valid_transfer_is_atomic(self):
        self.assert_rejected_unchanged({
            "balances": {"a": 5, "b": 0},
            "transfers": [["a", "b", 3], ["a", "b", 3]],
        })
        self.assert_rejected_unchanged({
            "balances": {"a": 5, "b": 0},
            "transfers": [["a", "b", 3], ["a", "missing", 0]],
        })

    def test_self_transfer_checks_current_balance(self):
        payload = {"balances": {"a": 5}, "transfers": [["a", "a", 5]]}
        self.assertEqual(process(payload), {"balances": {"a": 5}})
        self.assert_rejected_unchanged({
            "balances": {"a": 5}, "transfers": [["a", "a", 6]],
        })
        self.assert_rejected_unchanged({
            "balances": {"a": 5, "b": 0},
            "transfers": [["a", "b", 3], ["a", "a", 3]],
        })

    def test_zero_empty_unicode_and_extra_keys(self):
        self.assertEqual(process({"balances": {}, "transfers": [], "extra": 1}),
                         {"balances": {}})
        payload = {"balances": {"ø": 0, " ": 0},
                   "transfers": [["ø", " ", 0], ["ø", "ø", 0]]}
        self.assertEqual(process(payload), {"balances": {"ø": 0, " ": 0}})

    def test_unbounded_integer_arithmetic_and_exact_funds(self):
        amount = 10 ** 100
        self.assertEqual(process({
            "balances": {"a": amount, "b": amount},
            "transfers": [["a", "b", amount]],
        }), {"balances": {"a": 0, "b": 2 * amount}})

    def test_invalid_payload_shapes(self):
        invalid = [None, False, 0, "", [], (), {},
                   {"balances": {}}, {"transfers": []},
                   {"balances": [], "transfers": []},
                   {"balances": None, "transfers": []},
                   {"balances": {}, "transfers": None},
                   {"balances": {}, "transfers": {}},
                   {"balances": {}, "transfers": ()},
                   {"balances": {}, "transfers": ""}]
        for payload in invalid:
            self.assert_rejected_unchanged(payload)

    def test_invalid_balances_and_names(self):
        for value in (True, False, -1, 1.0, "1", None, [], {}):
            self.assert_rejected_unchanged({
                "balances": {"a": value}, "transfers": [],
            })
        for name in ("", 1, None, False, ("a",)):
            self.assert_rejected_unchanged({
                "balances": {name: 0}, "transfers": [],
            })

    def test_invalid_transfer_shapes(self):
        for transfer in (None, "abc", {}, (), ("a", "b", 1),
                         [], ["a"], ["a", "b"], ["a", "b", 1, 2]):
            self.assert_rejected_unchanged({
                "balances": {"a": 5, "b": 0}, "transfers": [transfer],
            })

    def test_invalid_amounts(self):
        for amount in (True, False, -1, 1.0, "1", None, [], {}):
            self.assert_rejected_unchanged({
                "balances": {"a": 5, "b": 0},
                "transfers": [["a", "b", amount]],
            })

    def test_invalid_transfer_accounts_including_zero_amount(self):
        for name in ("", "missing", 1, None, False, [], {}):
            for transfer in ([name, "b", 0], ["a", name, 0]):
                self.assert_rejected_unchanged({
                    "balances": {"a": 5, "b": 0}, "transfers": [transfer],
                })


class Batch(unittest.TestCase):
    def test_empty_and_ordered_results(self):
        self.assertEqual(service.batch([]), [])
        payloads = [
            {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
            {"balances": {"a": 10, "b": 2}, "transfers": [["b", "a", 2]]},
        ]
        before = copy.deepcopy(payloads)
        result = service.batch(payloads)
        self.assertEqual(result, [{"balances": {"a": 2, "b": 3}},
                                  {"balances": {"a": 12, "b": 0}}])
        self.assertEqual(payloads, before)
        result[0]["balances"]["a"] = 999
        self.assertEqual(payloads, before)

    def test_repeated_member_results_are_independent(self):
        payload = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        results = service.batch([payload, payload])
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}}] * 2)
        results[0]["balances"]["a"] = 999
        self.assertEqual(results[1], {"balances": {"a": 2, "b": 3}})
        self.assertEqual(payload["balances"], {"a": 5, "b": 0})

    def test_non_list_rejected(self):
        for payloads in (None, False, 0, "", {}, (), iter([])):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_member_rejects_entire_batch_without_mutation(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        for invalid in (None, [], {},
                        {"balances": {"a": True}, "transfers": []},
                        {"balances": {"a": 5, "b": 0},
                         "transfers": [["a", "b", 3], ["a", "a", 3]]}):
            for payloads in ([invalid, valid], [valid, invalid]):
                with self.subTest(payloads=payloads):
                    before = copy.deepcopy(payloads)
                    with self.assertRaises(ValueError):
                        service.batch(payloads)
                    self.assertEqual(payloads, before)


class CLI(unittest.TestCase):
    def run_cli(self, args=(), stdin=""):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=stdin, capture_output=True,
                              text=True, timeout=5)

    def test_json_transfers(self):
        payload = {"balances": {"ø": 5, "b": 0},
                   "transfers": [["ø", "b", 3]], "extra": True}
        result = self.run_cli(stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"balances": {"ø": 2, "b": 3}})

    def test_invalid_requests_produce_no_partial_stdout(self):
        for stdin in ("not json", "null", json.dumps({
            "balances": {"a": 5, "b": 0},
            "transfers": [["a", "b", 3], ["a", "a", 3]],
        })):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin=stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_preserved(self):
        for args in (["--unknown"], ["--version", "extra"], ["input.json"]):
            with self.subTest(args=args):
                result = self.run_cli(args, stdin="not json")
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

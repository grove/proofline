import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Transfers(unittest.TestCase):
    def assert_rejected(self, payload):
        original = copy.deepcopy(payload)
        for entry_point in (app.process, service.handle):
            with self.subTest(entry_point=entry_point.__name__):
                with self.assertRaises(ValueError):
                    entry_point(payload)
                self.assertEqual(payload, original)

    def test_ordered_transfers_and_input_immutability(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 0},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 1]],
            "extra": {"allowed": True},
        }
        original = copy.deepcopy(payload)
        expected = {"balances": {"a": 1, "b": 2, "c": 2}}
        for entry_point in (app.process, service.handle):
            result = entry_point(payload)
            self.assertEqual(result, expected)
            self.assertEqual(payload, original)
            result["balances"]["a"] = 100
            self.assertEqual(payload, original)

    def test_empty_and_zero_transfers(self):
        self.assertEqual(app.process({"balances": {}, "transfers": []}),
                         {"balances": {}})
        self.assertEqual(app.process({"balances": {"a": 0, "b": 0},
                                      "transfers": [["a", "b", 0]]}),
                         {"balances": {"a": 0, "b": 0}})

    def test_self_transfers_check_available_funds(self):
        for amount in (0, 5):
            self.assertEqual(app.process({"balances": {"a": 5},
                                          "transfers": [["a", "a", amount]]}),
                             {"balances": {"a": 5}})
        self.assert_rejected({"balances": {"a": 5},
                              "transfers": [["a", "a", 6]]})

    def test_intermediate_insufficient_funds_reject_atomically(self):
        self.assert_rejected({"balances": {"a": 5, "b": 0},
                              "transfers": [["a", "b", 3], ["a", "b", 3],
                                            ["b", "a", 6]]})
        self.assert_rejected({"balances": {"a": 0, "b": 5},
                              "transfers": [["a", "b", 1], ["b", "a", 5]]})

    def test_invalid_payload_shapes(self):
        for payload in (None, True, 1, "payload", [], {},
                        {"balances": {}}, {"transfers": []},
                        {"balances": [], "transfers": []},
                        {"balances": {}, "transfers": {}},
                        {"balances": {}, "transfers": ()}):
            with self.subTest(payload=payload):
                self.assert_rejected(payload)

    def test_invalid_balances(self):
        for name in ("", 1, None, False):
            with self.subTest(name=name):
                self.assert_rejected({"balances": {name: 0}, "transfers": []})
        for balance in (-1, True, False, 1.0, "1", None, [], {}):
            with self.subTest(balance=balance):
                self.assert_rejected({"balances": {"a": balance}, "transfers": []})

    def test_invalid_transfers(self):
        invalid_transfers = [None, {}, "abc", (), [], ["a", "b"],
                             ["a", "b", 1, 2], ("a", "b", 1)]
        invalid_transfers += [["a", "b", amount]
                              for amount in (-1, True, False, 1.0, "1", None, [], {})]
        invalid_transfers += [[name, "b", 0] for name in ("", "missing", 1, None, [], {})]
        invalid_transfers += [["a", name, 0] for name in ("", "missing", 1, None, [], {})]
        for transfer in invalid_transfers:
            with self.subTest(transfer=transfer):
                # A valid earlier transfer must not leak changes on rejection.
                self.assert_rejected({"balances": {"a": 5, "b": 0},
                                      "transfers": [["a", "b", 1], transfer]})

    def test_large_integers_and_unicode_names(self):
        amount = 10 ** 100
        self.assertEqual(app.process({"balances": {"源": amount, "目": 0},
                                      "transfers": [["源", "目", amount]]}),
                         {"balances": {"源": 0, "目": amount}})


class Batch(unittest.TestCase):
    def test_results_in_input_order(self):
        payloads = [{"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
                    {"balances": {"a": 1}, "transfers": []}]
        original = copy.deepcopy(payloads)
        results = service.batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}},
                                   {"balances": {"a": 1}}])
        results[0]["balances"]["a"] = 99
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_non_list_rejected(self):
        for payloads in (None, {}, (), "payloads", 1, True):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_member_rejects_without_mutation(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        invalid = {"balances": {"a": 1}, "transfers": [["a", "a", 2]]}
        for payloads in ([valid, invalid], [invalid, valid], [valid, None]):
            original = copy.deepcopy(payloads)
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)
            self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, stdin="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_success(self):
        result = self.run_cli(json.dumps({"balances": {"a": 5, "b": 0},
                                          "transfers": [["a", "b", 3]]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"balances": {"a": 2, "b": 3}})
        self.assertEqual(result.stderr, "")

    def test_rejection_has_no_partial_stdout(self):
        result = self.run_cli(json.dumps({"balances": {"a": 5, "b": 0},
                                          "transfers": [["a", "b", 3], ["a", "b", 3]]}))
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_unchanged(self):
        for args in (("--unknown",), ("--version", "extra")):
            result = self.run_cli(args=args)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

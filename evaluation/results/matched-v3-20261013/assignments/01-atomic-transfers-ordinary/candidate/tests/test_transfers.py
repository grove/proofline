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
        for entrypoint in (app.process, service.handle):
            with self.subTest(entrypoint=entrypoint.__name__):
                with self.assertRaises(ValueError):
                    entrypoint(payload)
                self.assertEqual(payload, original)

    def test_order_and_input_independence(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 1},
            "transfers": [["a", "b", 3], ["b", "c", 2]],
            "extra": {"ignored": True},
        }
        original = copy.deepcopy(payload)
        expected = {"balances": {"a": 2, "b": 1, "c": 3}}
        for entrypoint in (app.process, service.handle):
            result = entrypoint(payload)
            self.assertEqual(result, expected)
            self.assertIsNot(result["balances"], payload["balances"])
            result["balances"]["a"] = 100
            self.assertEqual(payload, original)

    def test_empty_zero_and_self_transfers(self):
        self.assertEqual(app.process({"balances": {}, "transfers": []}),
                         {"balances": {}})
        payload = {"balances": {"a": 5, "b": 0},
                   "transfers": [["a", "a", 5], ["b", "a", 0]]}
        self.assertEqual(app.process(payload), {"balances": {"a": 5, "b": 0}})

    def test_intermediate_insufficient_funds_and_self_transfer(self):
        for transfers in (
            [["a", "b", 3], ["a", "b", 3], ["b", "a", 3]],
            [["a", "b", 3], ["b", "b", 4]],
            [["a", "a", 6]],
        ):
            with self.subTest(transfers=transfers):
                self.assert_rejected({"balances": {"a": 5, "b": 0},
                                      "transfers": transfers})

    def test_invalid_payload_and_containers(self):
        for payload in (None, [], 1, "payload", {}, {"balances": {}},
                        {"transfers": []},
                        {"balances": [], "transfers": []},
                        {"balances": {}, "transfers": {}},
                        {"balances": {}, "transfers": ()}):
            with self.subTest(payload=payload):
                self.assert_rejected(payload)

    def test_invalid_balance_names_and_values(self):
        for name in ("", 1, None, False):
            with self.subTest(name=name):
                self.assert_rejected({"balances": {name: 1}, "transfers": []})
        for balance in (-1, True, False, 1.0, "1", None, [], {}):
            with self.subTest(balance=balance):
                self.assert_rejected({"balances": {"a": balance},
                                      "transfers": []})

    def test_invalid_transfers_after_valid_transfer(self):
        malformed = [None, {}, "abc", (), ("a", "b", 1), [],
                     ["a", "b"], ["a", "b", 1, 2]]
        for name in ("", "missing", 1, None, False, [], {}):
            malformed.extend(([name, "b", 0], ["a", name, 0]))
        for amount in (-1, True, False, 1.0, "1", None, [], {}):
            malformed.append(["a", "b", amount])
        for transfer in malformed:
            with self.subTest(transfer=transfer):
                self.assert_rejected({"balances": {"a": 5, "b": 0},
                                      "transfers": [["a", "b", 1], transfer]})

    def test_large_integer_and_unicode_names(self):
        amount = 10 ** 100
        self.assertEqual(app.process({"balances": {"账户": amount, "ø": 0},
                                      "transfers": [["账户", "ø", amount]]}),
                         {"balances": {"账户": 0, "ø": amount}})


class Batch(unittest.TestCase):
    def test_order_empty_and_repeated_payload(self):
        payload = {"balances": {"a": 5, "b": 0},
                   "transfers": [["a", "b", 3]]}
        payloads = [payload, {"balances": {"c": 1}, "transfers": []}, payload]
        original = copy.deepcopy(payloads)
        results = service.batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}},
                                   {"balances": {"c": 1}},
                                   {"balances": {"a": 2, "b": 3}}])
        self.assertEqual(payloads, original)
        results[0]["balances"]["a"] = 99
        self.assertEqual(results[2]["balances"]["a"], 2)
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_invalid_container_and_member_are_value_errors(self):
        valid = {"balances": {"a": 1}, "transfers": []}
        for payloads in (None, {}, "", (), [valid, None],
                         [valid, {"balances": {"a": True}, "transfers": []}],
                         [valid, {"balances": {"a": 1},
                                  "transfers": [["a", "a", 2]]}]):
            original = copy.deepcopy(payloads)
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    service.batch(payloads)
                self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, stdin="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=stdin, capture_output=True,
                              text=True, timeout=5)

    def test_json_success(self):
        result = self.run_cli(json.dumps({"balances": {"a": 5, "b": 0},
                                         "transfers": [["a", "b", 3]]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"balances": {"a": 2, "b": 3}})
        self.assertEqual(result.stderr, "")

    def test_rejection_has_no_partial_output(self):
        for stdin in ("{", json.dumps({"balances": {"a": 5, "b": 0},
                                       "transfers": [["a", "b", 3],
                                                     ["a", "b", 3]]})):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra")):
            with self.subTest(args=args):
                result = self.run_cli(args=args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

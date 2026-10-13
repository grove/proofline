import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
import service


class Transfers(unittest.TestCase):
    def assert_rejected_without_mutation(self, payload):
        original = copy.deepcopy(payload)
        for entrypoint in (process, service.handle):
            with self.subTest(entrypoint=entrypoint.__name__):
                with self.assertRaises(ValueError):
                    entrypoint(payload)
                self.assertEqual(payload, original)

    def test_order_and_input_isolation(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 0},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 2]],
            "extra": {"ignored": True},
        }
        original = copy.deepcopy(payload)
        for entrypoint in (process, service.handle):
            result = entrypoint(payload)
            self.assertEqual(result, {"balances": {"a": 2, "b": 2, "c": 1}})
            self.assertEqual(payload, original)
            result["balances"]["a"] = 99
            self.assertEqual(payload, original)

    def test_empty_zero_and_self_transfers(self):
        self.assertEqual(process({"balances": {}, "transfers": []}), {"balances": {}})
        payload = {"balances": {"a": 5, "b": 0},
                   "transfers": [["a", "a", 5], ["b", "a", 0], ["b", "b", 0]]}
        self.assertEqual(process(payload), {"balances": {"a": 5, "b": 0}})

    def test_insufficient_funds_and_late_errors_are_atomic(self):
        for transfers in (
            [["a", "b", 6]],
            [["a", "a", 6]],
            [["a", "b", 4], ["a", "b", 2]],
            [["b", "a", 1], ["a", "b", 1]],
            [["a", "b", 1], ["a", "missing", 0]],
            [["a", "b", 1], ["a", "b", True]],
            [["a", "b", 1], None],
        ):
            with self.subTest(transfers=transfers):
                self.assert_rejected_without_mutation(
                    {"balances": {"a": 5, "b": 0}, "transfers": transfers})

    def test_invalid_payload_shapes(self):
        for payload in (None, [], "text", 1, True, {}, {"balances": {}},
                        {"transfers": []}, {"balances": [], "transfers": []},
                        {"balances": {}, "transfers": {}},
                        {"balances": {}, "transfers": ()}):
            with self.subTest(payload=payload):
                self.assert_rejected_without_mutation(payload)

    def test_invalid_balances(self):
        for name in ("", 1, None, False):
            with self.subTest(name=name):
                self.assert_rejected_without_mutation(
                    {"balances": {name: 0}, "transfers": []})
        for balance in (-1, True, False, 1.0, "1", None, [], {}):
            with self.subTest(balance=balance):
                self.assert_rejected_without_mutation(
                    {"balances": {"a": balance}, "transfers": []})

    def test_invalid_transfers(self):
        invalid = [None, {}, "abc", [], ["a", "b"], ["a", "b", 0, 1],
                   ("a", "b", 0)]
        invalid += [["a", "b", amount] for amount in
                    (-1, True, False, 1.0, "1", None, [], {})]
        for name in ("", "missing", 1, None, False, [], {}):
            invalid.extend(([name, "b", 0], ["a", name, 0]))
        for transfer in invalid:
            with self.subTest(transfer=transfer):
                self.assert_rejected_without_mutation(
                    {"balances": {"a": 5, "b": 0}, "transfers": [transfer]})

    def test_unicode_names_and_large_integers(self):
        amount = 10 ** 100
        self.assertEqual(
            process({"balances": {"α": amount, "账户": 0},
                     "transfers": [["α", "账户", amount]]}),
            {"balances": {"α": 0, "账户": amount}})


class Batch(unittest.TestCase):
    def test_order_and_input_isolation(self):
        payloads = [
            {"balances": {"a": 2, "b": 0}, "transfers": [["a", "b", 1]]},
            {"balances": {"a": 9}, "transfers": []},
        ]
        original = copy.deepcopy(payloads)
        results = service.batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 1, "b": 1}},
                                   {"balances": {"a": 9}}])
        results[0]["balances"]["a"] = 100
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_rejects_nonlists(self):
        for payloads in (None, {}, (), "text", 1):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_member_keeps_entire_input_unchanged(self):
        valid = {"balances": {"a": 2, "b": 0}, "transfers": [["a", "b", 1]]}
        for invalid in (None, {}, {"balances": {"a": 0},
                                   "transfers": [["a", "a", 1]]}):
            payloads = [valid, invalid]
            original = copy.deepcopy(payloads)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                service.batch(payloads)
            self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def invoke(self, stdin="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_json_transfer(self):
        result = self.invoke(json.dumps({"balances": {"a": 5, "b": 0},
                                         "transfers": [["a", "b", 3]]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"balances": {"a": 2, "b": 3}})
        self.assertEqual(result.stderr, "")

    def test_rejection_has_no_partial_output(self):
        for stdin in ("{", "null", json.dumps({"balances": {"a": 5, "b": 0},
                                              "transfers": [["a", "b", 2],
                                                            ["a", "b", 4]]})):
            with self.subTest(stdin=stdin):
                result = self.invoke(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra")):
            with self.subTest(args=args):
                result = self.invoke(args=args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

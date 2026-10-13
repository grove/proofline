import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
from service import batch, handle


class Transfers(unittest.TestCase):
    def assert_rejected_unchanged(self, payload):
        original = copy.deepcopy(payload)
        for entrypoint in (process, handle):
            with self.subTest(entrypoint=entrypoint.__name__, payload=payload):
                with self.assertRaises(ValueError):
                    entrypoint(payload)
                self.assertEqual(payload, original)

    def test_ordered_transfers_and_independent_result(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 0},
            "transfers": [["a", "b", 5], ["b", "c", 4], ["c", "a", 2]],
            "extra": {"allowed": True},
        }
        original = copy.deepcopy(payload)
        for entrypoint in (process, handle):
            result = entrypoint(payload)
            self.assertEqual(result, {"balances": {"a": 2, "b": 1, "c": 2}})
            result["balances"]["a"] = 99
            self.assertEqual(payload, original)

    def test_empty_zero_self_and_large_integer_transfers(self):
        self.assertEqual(process({"balances": {}, "transfers": []}), {"balances": {}})
        amount = 10 ** 100
        payload = {"balances": {"α": amount, "β": 0}, "transfers": [
            ["β", "α", 0], ["α", "α", amount], ["α", "β", amount],
        ]}
        self.assertEqual(process(payload), {"balances": {"α": 0, "β": amount}})

    def test_rejects_insufficient_funds_at_intermediate_step(self):
        for transfers in (
            [["a", "b", 6], ["b", "a", 6]],
            [["a", "b", 3], ["a", "b", 3]],
            [["a", "b", 3], ["b", "b", 4]],
            [["a", "a", 6]],
        ):
            self.assert_rejected_unchanged({"balances": {"a": 5, "b": 0},
                                            "transfers": transfers})

    def test_invalid_payloads(self):
        for payload in (None, [], "value", 1, True, {}, {"balances": {}},
                        {"transfers": []}, {"balances": [], "transfers": []},
                        {"balances": {}, "transfers": {}},
                        {"balances": {}, "transfers": ()}):
            self.assert_rejected_unchanged(payload)

    def test_invalid_balances(self):
        for name in ("", 1, None, ("a",)):
            self.assert_rejected_unchanged({"balances": {name: 0}, "transfers": []})
        for value in (True, False, -1, 1.0, "1", None, [], {}):
            self.assert_rejected_unchanged({"balances": {"a": value}, "transfers": []})

    def test_invalid_transfer_members_after_valid_transfer(self):
        invalid = [None, {}, "abc", [], ["a", "b"], ["a", "b", 0, 1],
                   ("a", "b", 1)]
        for endpoint in ("", "missing", None, True, 1, [], {}):
            invalid.extend([[endpoint, "b", 0], ["a", endpoint, 0]])
        for amount in (True, False, -1, 1.0, "1", None, [], {}):
            invalid.append(["a", "b", amount])
        for transfer in invalid:
            self.assert_rejected_unchanged({"balances": {"a": 5, "b": 0},
                                            "transfers": [["a", "b", 1], transfer]})


class Batch(unittest.TestCase):
    def test_results_in_order_and_no_mutation(self):
        payload = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        payloads = [payload, {"balances": {}, "transfers": []}, payload]
        original = copy.deepcopy(payloads)
        results = batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}},
                                   {"balances": {}}, {"balances": {"a": 2, "b": 3}}])
        results[0]["balances"]["a"] = 100
        self.assertEqual(results[2]["balances"]["a"], 2)
        self.assertEqual(payloads, original)
        self.assertEqual(batch([]), [])

    def test_invalid_batch_or_member(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        for payloads in (None, {}, (), "value", 1, [valid, None],
                         [valid, {"balances": {"a": 0}, "transfers": [["a", "a", 1]]}]):
            original = copy.deepcopy(payloads)
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    batch(payloads)
                self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, payload, *args):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=payload, capture_output=True,
                              text=True, timeout=5)

    def test_json_transfer(self):
        result = self.run_cli(json.dumps({"balances": {"α": 5, "β": 0},
                                         "transfers": [["α", "β", 3]]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"balances": {"α": 2, "β": 3}})
        self.assertEqual(result.stderr, "")

    def test_error_has_no_partial_stdout(self):
        for payload in ('{"balances":{"a":5,"b":0},"transfers":'
                        '[["a","b",3],["a","b",3]]}', "{", "null"):
            result = self.run_cli(payload)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra"), ("--version", "--version")):
            result = self.run_cli("", *args)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (2, "", "ERROR: unsupported arguments\n"))

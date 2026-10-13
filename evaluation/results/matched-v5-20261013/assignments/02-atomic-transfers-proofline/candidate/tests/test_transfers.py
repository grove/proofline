import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Transfers(unittest.TestCase):
    def test_order_and_input_preservation(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 1},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 4]],
            "extra": {"ignored": True},
        }
        original = copy.deepcopy(payload)
        for entrypoint in (app.process, service.handle):
            result = entrypoint(payload)
            self.assertEqual(result, {"balances": {"a": 4, "b": 2, "c": 0}})
            self.assertEqual(payload, original)
            result["balances"]["a"] = 100
            self.assertEqual(payload, original)

    def test_self_transfer_and_zero_amount(self):
        self.assertEqual(
            app.process({"balances": {"a": 5, "b": 0},
                         "transfers": [["a", "a", 5], ["b", "a", 0]]}),
            {"balances": {"a": 5, "b": 0}},
        )

    def test_empty_accounts_and_arbitrary_precision(self):
        self.assertEqual(app.process({"balances": {}, "transfers": []}),
                         {"balances": {}})
        amount = 10 ** 100
        self.assertEqual(
            app.process({"balances": {"源": amount, "目标": 0},
                         "transfers": [["源", "目标", amount]]}),
            {"balances": {"源": 0, "目标": amount}},
        )

    def test_invalid_shapes(self):
        payloads = [
            None, [], "payload", 1, True, {},
            {"balances": {}, "transfers": None},
            {"balances": [], "transfers": []},
            {"balances": {}, "transfers": ()},
        ]
        payloads.extend({"balances": {"a": 5}, "transfers": [transfer]}
                        for transfer in (None, {}, "aaa", [], ["a", "a"],
                                         ["a", "a", 1, 2], ("a", "a", 1)))
        self.assert_rejected_without_mutation(payloads)

    def test_invalid_names_balances_and_amounts(self):
        payloads = []
        for name in ("", 1, None, True):
            payloads.append({"balances": {name: 5}, "transfers": []})
        for value in (True, False, -1, 1.0, "1", None, [], {}):
            payloads.append({"balances": {"a": value}, "transfers": []})
            payloads.append({"balances": {"a": 5},
                             "transfers": [["a", "a", value]]})
        for name in ("", "missing", 1, True, None, [], {}):
            payloads.append({"balances": {"a": 5},
                             "transfers": [[name, "a", 0]]})
            payloads.append({"balances": {"a": 5},
                             "transfers": [["a", name, 0]]})
        self.assert_rejected_without_mutation(payloads)

    def test_intermediate_rejection_is_atomic(self):
        payloads = [
            {"balances": {"a": 5}, "transfers": [["a", "a", 6]]},
            {"balances": {"a": 5, "b": 0},
             "transfers": [["b", "a", 1], ["a", "b", 1]]},
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 4], ["a", "b", 2]]},
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 4], ["a", "missing", 0]]},
        ]
        self.assert_rejected_without_mutation(payloads)

    def assert_rejected_without_mutation(self, payloads):
        for payload in payloads:
            for entrypoint in (app.process, service.handle):
                with self.subTest(payload=payload, entrypoint=entrypoint.__name__):
                    original = copy.deepcopy(payload)
                    with self.assertRaises(ValueError):
                        entrypoint(payload)
                    self.assertEqual(payload, original)


class Batch(unittest.TestCase):
    def test_order_and_independent_results(self):
        first = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        second = {"balances": {"x": 7}, "transfers": []}
        payloads = [first, second, first]
        original = copy.deepcopy(payloads)
        results = service.batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}},
                                   {"balances": {"x": 7}},
                                   {"balances": {"a": 2, "b": 3}}])
        results[0]["balances"]["a"] = 100
        self.assertEqual(results[2]["balances"]["a"], 2)
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_invalid_batch_is_atomic(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        invalid = {"balances": {"a": 0}, "transfers": [["a", "a", 1]]}
        for payloads in (None, {}, (), "batch", 1, [valid, None],
                         [valid, invalid], [invalid, valid]):
            with self.subTest(payloads=payloads):
                original = copy.deepcopy(payloads)
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

    def test_rejection_has_no_partial_stdout(self):
        for stdin in ("{", json.dumps({"balances": {"a": 5, "b": 0},
                                      "transfers": [["a", "b", 4], ["a", "b", 2]]})):
            result = self.run_cli(stdin)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra")):
            result = self.run_cli(args=args)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (2, "", "ERROR: unsupported arguments\n"))

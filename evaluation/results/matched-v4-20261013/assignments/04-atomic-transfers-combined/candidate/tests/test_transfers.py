import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Transfers(unittest.TestCase):
    def test_ordered_transfers_and_input_independence(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 1},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 4]],
            "extra": {"keep": [1, 2]},
        }
        snapshot = copy.deepcopy(payload)
        expected = {"balances": {"a": 4, "b": 2, "c": 0}}
        for entrypoint in (app.process, service.handle):
            with self.subTest(entrypoint=entrypoint.__name__):
                result = entrypoint(payload)
                self.assertEqual(result, expected)
                self.assertEqual(payload, snapshot)
                result["balances"]["a"] = 99
                self.assertEqual(payload, snapshot)

    def test_empty_zero_self_transfer_and_extra_keys(self):
        cases = [
            ({"balances": {}, "transfers": []}, {"balances": {}}),
            ({"balances": {"a": 0}, "transfers": [["a", "a", 0]]},
             {"balances": {"a": 0}}),
            ({"balances": {"a": 5}, "transfers": [["a", "a", 5]]},
             {"balances": {"a": 5}}),
            ({"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 0]]},
             {"balances": {"a": 5, "b": 0}}),
            ({"balances": {"å": 10**100, " ": 0},
              "transfers": [["å", " ", 10**100]], "ignored": False},
             {"balances": {"å": 0, " ": 10**100}}),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                snapshot = copy.deepcopy(payload)
                self.assertEqual(app.process(payload), expected)
                self.assertEqual(payload, snapshot)

    def test_intermediate_overdraft_and_excessive_self_transfer(self):
        for transfers in (
            [["a", "b", 6], ["b", "a", 6]],
            [["a", "b", 5], ["a", "b", 1]],
            [["a", "a", 6]],
        ):
            payload = {"balances": {"a": 5, "b": 10}, "transfers": transfers}
            snapshot = copy.deepcopy(payload)
            for entrypoint in (app.process, service.handle):
                with self.subTest(transfers=transfers, entrypoint=entrypoint.__name__):
                    with self.assertRaises(ValueError):
                        entrypoint(payload)
                    self.assertEqual(payload, snapshot)

    def test_invalid_payloads_reject_without_mutation_at_each_service_seam(self):
        invalid = [
            None, True, 1, "payload", [], (), {},
            {"balances": {}}, {"transfers": []},
        ]
        for balances in (None, [], "a", 1, True, {"": 0}, {1: 0}, {None: 0}):
            invalid.append({"balances": balances, "transfers": []})
        for balance in (-1, True, False, 1.0, "1", None, [], {}):
            invalid.append({"balances": {"a": balance}, "transfers": []})
        for transfers in (None, {}, "", (), True, 1):
            invalid.append({"balances": {"a": 5}, "transfers": transfers})
        for transfer in (
            None, {}, "abc", ("a", "b", 1), [], ["a"], ["a", "b"],
            ["a", "b", 1, "extra"],
            ["", "b", 1], ["a", "", 1], [[], "b", 1], ["a", {}, 1],
            [None, "b", 1], ["a", False, 1],
            ["missing", "b", 0], ["a", "missing", 0],
        ):
            invalid.append({"balances": {"a": 5, "b": 0}, "transfers": [transfer]})
        for amount in (-1, True, False, 1.0, "1", None, [], {}):
            invalid.append({"balances": {"a": 5, "b": 0},
                            "transfers": [["a", "b", amount]]})
        good = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        for payload in invalid:
            with self.subTest(payload=payload):
                snapshot = copy.deepcopy(payload)
                for entrypoint in (app.process, service.handle):
                    with self.assertRaises(ValueError):
                        entrypoint(payload)
                    self.assertEqual(payload, snapshot)
                batch = [copy.deepcopy(good), payload]
                batch_snapshot = copy.deepcopy(batch)
                with self.assertRaises(ValueError):
                    service.batch(batch)
                self.assertEqual(batch, batch_snapshot)

    def test_late_invalid_transfer_is_atomic(self):
        payload = {"balances": {"a": 5, "b": 0},
                   "transfers": [["a", "b", 3], ["a", "missing", 1]]}
        snapshot = copy.deepcopy(payload)
        with self.assertRaises(ValueError):
            app.process(payload)
        self.assertEqual(payload, snapshot)


class Batch(unittest.TestCase):
    def test_order_and_independent_results(self):
        first = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        second = {"balances": {"a": 1, "b": 8}, "transfers": [["b", "a", 5]]}
        payloads = [first, second, first]
        snapshot = copy.deepcopy(payloads)
        results = service.batch(payloads)
        self.assertEqual(results, [{"balances": {"a": 2, "b": 3}},
                                   {"balances": {"a": 6, "b": 3}},
                                   {"balances": {"a": 2, "b": 3}}])
        results[0]["balances"]["a"] = 99
        self.assertEqual(results[2], {"balances": {"a": 2, "b": 3}})
        self.assertEqual(payloads, snapshot)
        self.assertEqual(service.batch([]), [])

    def test_non_list_rejection(self):
        for payloads in (None, {}, (), "", True, 5, iter([])):
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    service.batch(payloads)

    def test_late_insufficient_funds_rejects_entire_batch(self):
        payloads = [
            {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
            {"balances": {"a": 1}, "transfers": [["a", "a", 2]]},
        ]
        snapshot = copy.deepcopy(payloads)
        with self.assertRaises(ValueError):
            service.batch(payloads)
        self.assertEqual(payloads, snapshot)


class Cli(unittest.TestCase):
    repo = pathlib.Path(__file__).resolve().parents[1]

    def run_cli(self, args=(), stdin=""):
        return subprocess.run([sys.executable, "-B", str(self.repo / "cli.py"), *args],
                              cwd=self.repo, input=stdin, capture_output=True,
                              text=True, timeout=5)

    def test_json_success(self):
        payload = {"balances": {"å": 5, "b": 0}, "transfers": [["å", "b", 3]]}
        result = self.run_cli(stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"balances": {"å": 2, "b": 3}})

    def test_rejection_has_no_partial_stdout(self):
        invalid = [None, {"balances": {"a": True}, "transfers": []},
                   {"balances": {"a": 5, "b": 0},
                    "transfers": [["a", "b", 3], ["a", "a", 3]]}]
        for payload in invalid:
            with self.subTest(payload=payload):
                result = self.run_cli(stdin=json.dumps(payload))
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_version_and_unsupported_arguments(self):
        version = self.run_cli(["--version"], stdin="invalid JSON")
        self.assertEqual((version.returncode, version.stdout, version.stderr),
                         (0, "api-v1\n", ""))
        for args in (["--help"], ["--version", "extra"], ["extra"],
                     ["--version", "--version"]):
            with self.subTest(args=args):
                result = self.run_cli(args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

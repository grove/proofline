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
        for handler in (app.process, service.handle):
            before = copy.deepcopy(payload)
            with self.subTest(handler=handler.__name__, payload=payload):
                with self.assertRaises(ValueError):
                    handler(payload)
                self.assertEqual(payload, before)

    def test_ordered_transfers_and_extra_keys(self):
        payload = {
            "balances": {"a": 5, "b": 0, "c": 0},
            "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 1]],
            "metadata": {"ignored": True},
        }
        before = copy.deepcopy(payload)
        expected = {"balances": {"a": 1, "b": 2, "c": 2}}
        for handler in (app.process, service.handle):
            self.assertEqual(handler(payload), expected)
            self.assertEqual(payload, before)

    def test_empty_zero_self_and_large_integer_transfers(self):
        self.assertEqual(app.process({"balances": {}, "transfers": []}),
                         {"balances": {}})
        large = 10 ** 100
        payload = {"balances": {"账户": large, "b": 0},
                   "transfers": [["账户", "账户", large], ["b", "账户", 0],
                                 ["账户", "b", large]]}
        self.assertEqual(app.process(payload), {"balances": {"账户": 0, "b": large}})

    def test_result_is_independent_of_input(self):
        payload = {"balances": {"a": 1}, "transfers": []}
        result = app.process(payload)
        result["balances"]["a"] = 9
        self.assertEqual(payload["balances"], {"a": 1})

    def test_insufficient_funds_at_intermediate_step(self):
        self.assert_rejected_without_mutation({
            "balances": {"a": 5, "b": 0},
            "transfers": [["a", "b", 3], ["a", "b", 3], ["b", "a", 3]],
        })
        self.assert_rejected_without_mutation({
            "balances": {"a": 5}, "transfers": [["a", "a", 6]],
        })

    def test_invalid_payload_shapes(self):
        for payload in (None, [], "text", 1, True, {},
                        {"balances": {}, "transfers": None},
                        {"balances": [], "transfers": []},
                        {"balances": {}, "transfers": ()}):
            self.assert_rejected_without_mutation(payload)

    def test_invalid_balances_and_names(self):
        for balance in (True, False, -1, 1.0, "1", None, [], {}):
            self.assert_rejected_without_mutation({
                "balances": {"a": balance}, "transfers": [],
            })
        for name in ("", 1, None, False):
            self.assert_rejected_without_mutation({
                "balances": {name: 1}, "transfers": [],
            })

    def test_invalid_transfers_after_valid_transfer(self):
        invalid = [None, {}, "abc", (), [], ["a", "b"],
                   ["a", "b", 0, 1], ("a", "b", 0),
                   ["missing", "b", 0], ["a", "missing", 0]]
        for amount in (True, False, -1, 1.0, "1", None, [], {}):
            invalid.append(["a", "b", amount])
        for name in ("", 1, None, False, [], {}):
            invalid.extend([[name, "b", 0], ["a", name, 0]])
        for transfer in invalid:
            self.assert_rejected_without_mutation({
                "balances": {"a": 5, "b": 0},
                "transfers": [["a", "b", 1], transfer],
            })


class Batch(unittest.TestCase):
    def test_batch_order_and_no_mutation(self):
        payloads = [
            {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
            {"balances": {"x": 10}, "transfers": []},
        ]
        before = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [
            {"balances": {"a": 2, "b": 3}}, {"balances": {"x": 10}},
        ])
        self.assertEqual(payloads, before)
        self.assertEqual(service.batch([]), [])

    def test_batch_rejection(self):
        for payloads in (None, {}, (), "text", 1):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)
        for invalid in (None, {}, {"balances": {"a": 1},
                                   "transfers": [["a", "a", 2]]}):
            payloads = [{"balances": {"a": 2, "b": 0},
                         "transfers": [["a", "b", 1]]}, invalid]
            before = copy.deepcopy(payloads)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                service.batch(payloads)
            self.assertEqual(payloads, before)


class CLI(unittest.TestCase):
    def run_cli(self, payload="", *arguments):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"),
                               *arguments], input=payload, cwd=repo,
                              capture_output=True, text=True, timeout=5)

    def test_json_transfers(self):
        result = self.run_cli(json.dumps({
            "balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]],
        }))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"balances": {"a": 2, "b": 3}})
        self.assertEqual(result.stderr, "")

    def test_invalid_input_has_no_result(self):
        for payload in ('{"balances":{"a":1},"transfers":[["a","a",2]]}',
                        '{"balances":{"a":true},"transfers":[]}', "invalid"):
            with self.subTest(payload=payload):
                result = self.run_cli(payload)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for arguments in (("--unknown",), ("--version", "extra")):
            result = self.run_cli("", *arguments)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (2, "", "ERROR: unsupported arguments\n"))

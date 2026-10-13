import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Transfers(unittest.TestCase):
    def assert_result(self, payload, expected):
        for entry in (app.process, service.handle):
            with self.subTest(entry=entry.__name__, payload=payload):
                before = copy.deepcopy(payload)
                result = entry(payload)
                self.assertEqual(result, expected)
                self.assertEqual(payload, before)
                self.assertIsNot(result["balances"], payload["balances"])

    def assert_invalid(self, payload):
        for entry in (app.process, service.handle):
            with self.subTest(entry=entry.__name__, payload=payload):
                before = copy.deepcopy(payload)
                with self.assertRaises(ValueError):
                    entry(payload)
                self.assertEqual(payload, before)

    def test_ordered_transfers(self):
        self.assert_result(
            {"balances": {"a": 5, "b": 0, "c": 1},
             "transfers": [["a", "b", 5], ["b", "c", 3], ["c", "a", 4]]},
            {"balances": {"a": 4, "b": 2, "c": 0}},
        )

    def test_empty_and_zero(self):
        self.assert_result({"balances": {}, "transfers": []}, {"balances": {}})
        self.assert_result(
            {"balances": {"a": 0, "b": 7},
             "transfers": [["a", "b", 0], ["a", "a", 0]]},
            {"balances": {"a": 0, "b": 7}},
        )

    def test_self_transfers(self):
        self.assert_result(
            {"balances": {"a": 5}, "transfers": [["a", "a", 5], ["a", "a", 3]]},
            {"balances": {"a": 5}},
        )
        self.assert_invalid({"balances": {"a": 5}, "transfers": [["a", "a", 6]]})
        self.assert_invalid({"balances": {"a": 0}, "transfers": [["a", "a", 1]]})

    def test_intermediate_overdraft_cannot_be_repaired(self):
        self.assert_invalid(
            {"balances": {"a": 0, "b": 5},
             "transfers": [["a", "b", 1], ["b", "a", 5]]}
        )
        self.assert_invalid(
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 3], ["a", "b", 3]]}
        )
        self.assert_invalid(
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 3], ["a", "a", 3]]}
        )

    def test_extra_keys_names_and_large_integers(self):
        large = 10 ** 100
        self.assert_result(
            {"balances": {"å": large, " ": 0},
             "transfers": [["å", " ", large]], "metadata": {"anything": [True]}},
            {"balances": {"å": 0, " ": large}},
        )

    def test_invalid_payload_and_container_shapes(self):
        for payload in (
            None, True, 1, 1.5, "", [], (), {},
            {"balances": {}}, {"transfers": []},
            {"balances": None, "transfers": []},
            {"balances": [], "transfers": []},
            {"balances": {}, "transfers": None},
            {"balances": {}, "transfers": ()},
            {"balances": {}, "transfers": {}},
            {"balances": {}, "transfers": ""},
        ):
            self.assert_invalid(payload)

    def test_invalid_balances(self):
        for name in ("", 0, False, None, ("a",)):
            self.assert_invalid({"balances": {name: 1}, "transfers": []})
        for balance in (-1, True, False, 1.0, "1", None, [], {}):
            self.assert_invalid({"balances": {"a": balance}, "transfers": []})

    def test_invalid_transfer_shapes(self):
        for transfer in (None, False, 1, "abc", {}, (), ("a", "b", 1),
                         [], ["a"], ["a", "b"], ["a", "b", 1, 0]):
            self.assert_invalid(
                {"balances": {"a": 5, "b": 0}, "transfers": [transfer]}
            )

    def test_invalid_endpoints_and_amounts(self):
        for name in ("", "missing", None, False, 0, [], {}):
            self.assert_invalid(
                {"balances": {"a": 5, "b": 0}, "transfers": [[name, "b", 0]]}
            )
            self.assert_invalid(
                {"balances": {"a": 5, "b": 0}, "transfers": [["a", name, 0]]}
            )
        for amount in (-1, True, False, 1.0, "1", None, [], {}):
            self.assert_invalid(
                {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", amount]]}
            )

    def test_invalid_later_transfer_leaves_input_unchanged(self):
        self.assert_invalid(
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 3], ["a", "missing", 0]]}
        )
        self.assert_invalid(
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 3], ["a", "b", True]]}
        )

    def test_result_cannot_mutate_input(self):
        payload = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        before = copy.deepcopy(payload)
        for entry in (app.process, service.handle):
            result = entry(payload)
            result["balances"]["a"] = -100
            result["balances"]["new"] = 10
            self.assertEqual(payload, before)


class Batch(unittest.TestCase):
    def test_results_in_input_order(self):
        payloads = [
            {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]},
            {"balances": {"x": 8}, "transfers": [["x", "x", 8]]},
            {"balances": {}, "transfers": []},
        ]
        before = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [
            {"balances": {"a": 2, "b": 3}},
            {"balances": {"x": 8}},
            {"balances": {}},
        ])
        self.assertEqual(payloads, before)
        self.assertEqual(service.batch([]), [])

    def test_invalid_container(self):
        for payloads in (None, False, 0, "", {}, (), iter([])):
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    service.batch(payloads)

    def test_invalid_member_rejects_entire_batch_without_mutation(self):
        valid = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        invalid_members = [
            None, [], {},
            {"balances": {"a": 0}, "transfers": [["a", "a", 1]]},
            {"balances": {"a": True}, "transfers": []},
        ]
        for invalid in invalid_members:
            for payloads in ([invalid, valid], [valid, invalid]):
                with self.subTest(payloads=payloads):
                    before = copy.deepcopy(payloads)
                    with self.assertRaises(ValueError):
                        service.batch(payloads)
                    self.assertEqual(payloads, before)

    def test_repeated_members_and_outputs_are_independent(self):
        payload = {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}
        before = copy.deepcopy(payload)
        results = service.batch([payload, payload])
        self.assertEqual(results, [
            {"balances": {"a": 2, "b": 3}}, {"balances": {"a": 2, "b": 3}},
        ])
        results[0]["balances"]["a"] = -1
        self.assertEqual(results[1], {"balances": {"a": 2, "b": 3}})
        self.assertEqual(payload, before)


class CLI(unittest.TestCase):
    def run_cli(self, text="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, "-B", str(repo / "cli.py"), *args],
            cwd=repo, input=text, capture_output=True, text=True, timeout=5,
        )

    def test_json_success(self):
        result = self.run_cli(json.dumps(
            {"balances": {"å": 5, "b": 0},
             "transfers": [["å", "b", 3], ["b", "å", 2]], "extra": True}
        ))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"balances": {"å": 4, "b": 1}})

    def test_rejection_has_no_partial_output(self):
        for payload in (
            {"balances": {"a": 5, "b": 0},
             "transfers": [["a", "b", 3], ["a", "b", 3]]},
            {"balances": {"a": 5}, "transfers": [["a", "a", 6]]},
            {"balances": {"a": True}, "transfers": []},
            None,
        ):
            with self.subTest(payload=payload):
                result = self.run_cli(json.dumps(payload))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_invalid_json(self):
        result = self.run_cli("{")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_are_unchanged(self):
        for args in (("--help",), ("extra",), ("--version", "extra")):
            with self.subTest(args=args):
                result = self.run_cli(args=args)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (2, "", "ERROR: unsupported arguments\n"),
                )


if __name__ == "__main__":
    unittest.main()

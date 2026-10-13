import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
import service


class FifoCache(unittest.TestCase):
    def test_update_keeps_original_position(self):
        payload = {"capacity": 3, "events": [
            {"id": "a", "value": 1}, {"id": "b", "value": 2},
            {"id": "c", "value": 3}, {"id": "b", "value": None},
            {"id": "a", "value": 4},
        ]}
        self.assertEqual(process(payload), {"items": [
            {"id": "a", "value": 4}, {"id": "b", "value": None},
            {"id": "c", "value": 3},
        ], "evicted": []})

    def test_eviction_and_reinsertion_retain_repetitions(self):
        payload = {"capacity": 1, "events": [
            {"id": identifier, "value": index}
            for index, identifier in enumerate(["a", "a", "b", "a", "b"])
        ]}
        self.assertEqual(process(payload), {
            "items": [{"id": "b", "value": 4}], "evicted": ["a", "b", "a"]})

    def test_zero_capacity_evicts_every_event(self):
        self.assertEqual(process({"capacity": 0, "events": [
            {"id": "a", "value": None}, {"id": "a", "value": 2},
            {"id": "b", "value": False},
        ]}), {"items": [], "evicted": ["a", "a", "b"]})

    def test_empty_events(self):
        for capacity in (0, 1, 100):
            with self.subTest(capacity=capacity):
                self.assertEqual(process({"capacity": capacity, "events": []}),
                                 {"items": [], "evicted": []})

    def test_json_values_and_extra_keys_do_not_change_input(self):
        values = [None, True, False, 42, -2.5, "", [1, {"x": None}],
                  {"nested": [True, "text"]}]
        payload = {"capacity": len(values), "extra": "ignored", "events": [
            {"id": str(i), "value": value, "extra": "ignored"}
            for i, value in enumerate(values)
        ]}
        original = copy.deepcopy(payload)
        expected = {"items": [{"id": str(i), "value": value}
                              for i, value in enumerate(values)], "evicted": []}
        self.assertEqual(process(payload), expected)
        self.assertEqual(service.handle(payload), expected)
        self.assertEqual(payload, original)

    def test_malformed_payloads_raise_value_error_without_mutation(self):
        invalid = [None, [], "payload", 1, {}, {"capacity": 1},
                   {"events": []}]
        invalid += [{"capacity": value, "events": []}
                    for value in (True, False, -1, 1.0, "1", None, [], {})]
        invalid += [{"capacity": 1, "events": value}
                    for value in (None, {}, "events", 1, ())]
        bad_events = [None, [], "event", 1, {}, {"id": "a"}, {"value": 1}]
        bad_events += [{"id": value, "value": 1}
                       for value in ("", None, True, 1, [], {})]
        invalid += [{"capacity": 1, "events": [
            {"id": "valid", "value": {"nested": [1, 2]}}, event]}
            for event in bad_events]
        for payload in invalid:
            with self.subTest(payload=payload):
                original = copy.deepcopy(payload)
                for entrypoint in (process, service.handle):
                    with self.assertRaises(ValueError):
                        entrypoint(payload)
                self.assertEqual(payload, original)

    def test_invalid_json_values(self):
        cyclic = []
        cyclic.append(cyclic)
        for value in (object(), {1: "bad key"}, (1, 2), {1},
                      float("nan"), float("inf"), cyclic):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ValueError):
                    process({"capacity": 1, "events": [{"id": "a", "value": value}]})

    def test_shared_json_container_is_valid(self):
        shared = {"nested": [1, None]}
        value = [shared, shared]
        self.assertEqual(process({"capacity": 1, "events": [
            {"id": "a", "value": value}]}),
            {"items": [{"id": "a", "value": value}], "evicted": []})

    def test_deep_json_values(self):
        value = None
        for _ in range(1500):
            value = [value]
        result = process({"capacity": 1, "events": [{"id": "a", "value": value}]})
        self.assertEqual(result["evicted"], [])
        self.assertEqual(result["items"][0]["id"], "a")
        self.assertIs(result["items"][0]["value"], value)


class Batch(unittest.TestCase):
    def test_batch_preserves_order_and_input(self):
        payloads = [{"capacity": 0, "events": [{"id": "a", "value": None}]},
                    {"capacity": 2, "events": [{"id": "b", "value": [1, 2]}]}]
        original = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [
            {"items": [], "evicted": ["a"]},
            {"items": [{"id": "b", "value": [1, 2]}], "evicted": []}])
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_invalid_batch_does_not_change_input(self):
        valid = {"capacity": 1, "events": [{"id": "a", "value": {"x": [1]}}]}
        for payloads in (None, {}, (), "batch", [valid, None],
                         [valid, {"capacity": True, "events": []}],
                         [valid, {"capacity": 1, "events": [{"id": "b"}]}]):
            with self.subTest(payloads=payloads):
                original = copy.deepcopy(payloads)
                with self.assertRaises(ValueError):
                    service.batch(payloads)
                self.assertEqual(payloads, original)


class Cli(unittest.TestCase):
    def run_cli(self, args=(), stdin=""):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=stdin, capture_output=True,
                              text=True, timeout=5)

    def test_json_stdin_stdout(self):
        payload = {"capacity": 1, "events": [{"id": "å", "value": None},
                                               {"id": "b", "value": [True]}]}
        result = self.run_cli(stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), process(payload))
        self.assertEqual(result.stderr, "")

    def test_invalid_input(self):
        for stdin in ("not json", '{"capacity": true, "events": []}',
                      '{"capacity": 1, "events": [{"id": "a"}]}'):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin=stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra"), ("--version", "--version")):
            with self.subTest(args=args):
                result = self.run_cli(args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
from service import batch, handle


class FifoBehavior(unittest.TestCase):
    def test_update_preserves_position_and_strips_extra_keys(self):
        payload = {
            "capacity": 3,
            "events": [
                {"id": "a", "value": 1, "extra": "ignored"},
                {"id": "b", "value": 2},
                {"id": "a", "value": None, "other": True},
                {"id": "c", "value": {"nested": [False, 1.5, "é"]}},
            ],
            "extra": "ignored",
        }
        before = copy.deepcopy(payload)
        expected = {
            "items": [
                {"id": "a", "value": None},
                {"id": "b", "value": 2},
                {"id": "c", "value": {"nested": [False, 1.5, "é"]}},
            ],
            "evicted": [],
        }
        self.assertEqual(process(payload), expected)
        self.assertEqual(handle(payload), expected)
        self.assertEqual(payload, before)

    def test_reinsertion_and_repeated_evictions(self):
        payload = {
            "capacity": 2,
            "events": [{"id": key, "value": index}
                       for index, key in enumerate("abacada")],
        }
        self.assertEqual(process(payload), {
            "items": [{"id": "a", "value": 6}, {"id": "d", "value": 5}],
            "evicted": ["a", "b", "c"],
        })
        single = {"capacity": 1, "events": [
            {"id": key, "value": None} for key in "ababa"
        ]}
        self.assertEqual(process(single), {
            "items": [{"id": "a", "value": None}],
            "evicted": ["a", "b", "a", "b"],
        })

    def test_zero_capacity_evicts_every_event(self):
        self.assertEqual(process({"capacity": 0, "events": [
            {"id": key, "value": None} for key in ["a", "a", "b", "a"]
        ]}), {"items": [], "evicted": ["a", "a", "b", "a"]})

    def test_empty_events(self):
        for capacity in [0, 1, 100]:
            self.assertEqual(process({"capacity": capacity, "events": []}),
                             {"items": [], "evicted": []})

    def test_malformed_payloads_and_records(self):
        invalid = [None, [], "payload", {},
                   {"events": []}, {"capacity": 1}]
        invalid.extend({"capacity": capacity, "events": []}
                       for capacity in [True, False, -1, 1.0, "1", None])
        invalid.extend({"capacity": 1, "events": events}
                       for events in [None, {}, (), "events"])
        bad_records = [None, [], "record", {}, {"id": "a"},
                       {"value": None}, {"id": "", "value": 0},
                       {"id": 1, "value": 0}, {"id": [], "value": 0}]
        invalid.extend({"capacity": 2, "events": [
            {"id": "valid", "value": {"nested": [1, None]}}, record
        ]} for record in bad_records)
        for payload in invalid:
            with self.subTest(payload=payload):
                before = copy.deepcopy(payload)
                for entrypoint in [process, handle]:
                    with self.assertRaises(ValueError):
                        entrypoint(payload)
                self.assertEqual(payload, before)

    def test_non_json_values_and_cycles_are_rejected(self):
        cyclic = []
        cyclic.append(cyclic)
        for value in [object(), (1, 2), {1: "bad key"}, {1, 2},
                      float("nan"), float("inf"), {"nested": [object()]}, cyclic]:
            with self.subTest(value_type=type(value)):
                with self.assertRaises(ValueError):
                    process({"capacity": 1, "events": [{"id": "a", "value": value}]})

    def test_shared_json_containers_are_valid(self):
        child = [None, {"x": True}]
        value = [child, child]
        self.assertEqual(process({"capacity": 1, "events": [
            {"id": "a", "value": value}
        ]}), {"items": [{"id": "a", "value": value}], "evicted": []})

    def test_batch_order_independence_and_validation(self):
        payloads = [
            {"capacity": 1, "events": [{"id": "a", "value": 1}]},
            {"capacity": 0, "events": [{"id": "a", "value": None}]},
            {"capacity": 3, "events": []},
        ]
        before = copy.deepcopy(payloads)
        self.assertEqual(batch(payloads), [
            {"items": [{"id": "a", "value": 1}], "evicted": []},
            {"items": [], "evicted": ["a"]},
            {"items": [], "evicted": []},
        ])
        self.assertEqual(payloads, before)
        self.assertEqual(batch([]), [])
        for invalid in [None, {}, (), "payloads", [payloads[0], {"capacity": True}]]:
            snapshot = copy.deepcopy(invalid)
            with self.subTest(payloads=invalid):
                with self.assertRaises(ValueError):
                    batch(invalid)
                self.assertEqual(invalid, snapshot)


class CliBehavior(unittest.TestCase):
    def run_cli(self, stdin="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              cwd=repo, input=stdin, capture_output=True,
                              text=True, timeout=5)

    def test_json_stdin_stdout(self):
        payload = {"capacity": 1, "events": [
            {"id": "a", "value": 1}, {"id": "é", "value": None}
        ]}
        result = self.run_cli(json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {
            "items": [{"id": "é", "value": None}], "evicted": ["a"]
        })

    def test_invalid_json_and_invalid_payload(self):
        for stdin in ["{", "null", '{"capacity": true, "events": []}',
                      '{"capacity": 1, "events": [{"id": "a"}]}']:
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in [("--unknown",), ("--version", "extra")]:
            result = self.run_cli(args=args)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (2, "", "ERROR: unsupported arguments\n"))

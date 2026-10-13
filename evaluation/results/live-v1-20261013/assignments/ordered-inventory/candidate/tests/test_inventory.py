import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Inventory(unittest.TestCase):
    def test_ordered_updates_retain_all_skus_and_zeros(self):
        payload = {
            "starting": {"existing": 2, "untouched": 0},
            "events": [
                {"sku": "new", "delta": 3},
                {"sku": "existing", "delta": -2},
                {"sku": "new", "delta": -3},
                {"sku": "visited", "delta": 0},
            ],
        }
        original = copy.deepcopy(payload)
        self.assertEqual(app.process(payload), {
            "stock": {"existing": 0, "untouched": 0, "new": 0, "visited": 0},
        })
        self.assertEqual(payload, original)

    def test_transient_negative_is_rejected(self):
        for starting in ({}, {"sku": 1}):
            with self.subTest(starting=starting), self.assertRaises(ValueError):
                app.process({"starting": starting, "events": [
                    {"sku": "sku", "delta": -2},
                    {"sku": "sku", "delta": 3},
                ]})

    def test_reversing_events_can_make_them_valid(self):
        self.assertEqual(app.process({"starting": {}, "events": [
            {"sku": "sku", "delta": 3},
            {"sku": "sku", "delta": -2},
        ]}), {"stock": {"sku": 1}})

    def test_empty_inventory(self):
        self.assertEqual(app.process({"starting": {}, "events": []}), {"stock": {}})

    def test_malformed_payloads(self):
        invalid = [
            None, [], "inventory", {}, {"starting": {}}, {"events": []},
            {"starting": {}, "events": [], "extra": 1},
            {"starting": [], "events": []},
            {"starting": {}, "events": {}},
            {"starting": {}, "events": None},
            {"starting": {}, "events": ()},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                app.process(payload)

    def test_invalid_starting_records(self):
        invalid = [
            {"": 0}, {1: 0}, {None: 0}, {"sku": -1}, {"sku": True},
            {"sku": False}, {"sku": 1.0}, {"sku": "1"}, {"sku": None},
            {"sku": []},
        ]
        for starting in invalid:
            with self.subTest(starting=starting), self.assertRaises(ValueError):
                app.process({"starting": starting, "events": []})

    def test_invalid_events(self):
        invalid = [
            None, [], "event", {}, {"sku": "sku"}, {"delta": 1},
            {"sku": "sku", "delta": 1, "extra": 1},
            {"sku": "", "delta": 1}, {"sku": 1, "delta": 1},
            {"sku": None, "delta": 1}, {"sku": [], "delta": 1},
            {"sku": "sku", "delta": True}, {"sku": "sku", "delta": False},
            {"sku": "sku", "delta": 1.0}, {"sku": "sku", "delta": "1"},
            {"sku": "sku", "delta": None}, {"sku": "sku", "delta": []},
        ]
        for event in invalid:
            with self.subTest(event=event), self.assertRaises(ValueError):
                app.process({"starting": {}, "events": [event]})

    def test_arbitrary_precision_and_unicode_skus(self):
        quantity = 10 ** 100
        self.assertEqual(app.process({"starting": {"\u00e6": quantity}, "events": [
            {"sku": "\u00e6", "delta": -quantity},
        ]}), {"stock": {"\u00e6": 0}})

    def test_service_delegates_and_propagates_validation(self):
        self.assertEqual(service.handle({"starting": {"sku": 2}, "events": []}),
                         {"stock": {"sku": 2}})
        with self.assertRaises(ValueError):
            service.handle({"starting": {}, "events": [{"sku": "sku", "delta": -1}]})

    def test_cli_success_and_validation_error(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        for payload, expected_code in [
            ({"starting": {"\u00e6": 1}, "events": [{"sku": "\u00e6", "delta": -1}]}, 0),
            ({"starting": {}, "events": [{"sku": "sku", "delta": -1}]}, 2),
        ]:
            with self.subTest(payload=payload):
                result = subprocess.run(
                    [sys.executable, "-B", str(repo / "cli.py")], cwd=repo,
                    input=json.dumps(payload), capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(result.returncode, expected_code)
                if expected_code == 0:
                    self.assertEqual(result.stdout, '{"stock": {"\u00e6": 0}}\n')
                    self.assertEqual(result.stderr, "")
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertTrue(result.stderr.startswith("ERROR: "))

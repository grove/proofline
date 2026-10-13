import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
import service


def payload(capacity, *events):
    return {"capacity": capacity,
            "events": [{"id": key, "value": value} for key, value in events]}


class FifoCache(unittest.TestCase):
    def test_update_keeps_position_and_latest_value(self):
        data = payload(3, ("a", 1), ("b", 2), ("c", 3), ("a", None))
        expected = {"items": [{"id": "a", "value": None},
                              {"id": "b", "value": 2},
                              {"id": "c", "value": 3}], "evicted": []}
        self.assertEqual(process(data), expected)
        data["events"].append({"id": "d", "value": 4})
        self.assertEqual(process(data), {
            "items": [{"id": "b", "value": 2},
                      {"id": "c", "value": 3},
                      {"id": "d", "value": 4}], "evicted": ["a"]})

    def test_reinsertions_and_repeated_evictions(self):
        data = payload(2, ("a", 1), ("b", 2), ("c", 3), ("a", 4),
                       ("d", 5), ("e", 6), ("a", 7))
        self.assertEqual(process(data), {
            "items": [{"id": "e", "value": 6}, {"id": "a", "value": 7}],
            "evicted": ["a", "b", "c", "a", "d"]})

    def test_zero_capacity_evicts_every_event(self):
        self.assertEqual(process(payload(0, ("a", 1), ("a", 2), ("b", None),
                                         ("a", 3))),
                         {"items": [], "evicted": ["a", "a", "b", "a"]})

    def test_empty_events(self):
        for capacity in (0, 1, 100):
            with self.subTest(capacity=capacity):
                self.assertEqual(process(payload(capacity)),
                                 {"items": [], "evicted": []})

    def test_json_values_extra_keys_and_nonempty_ids(self):
        values = [None, True, False, 0, -1, 2.5, "", [], {},
                  {"nested": [None, {"unicode": "æ"}]}]
        data = {"capacity": len(values), "extra": object(), "events": [
            {"id": str(index), "value": value, "ignored": object()}
            for index, value in enumerate(values)]}
        self.assertEqual(process(data), {
            "items": [{"id": str(index), "value": value}
                      for index, value in enumerate(values)], "evicted": []})
        self.assertEqual(process(payload(1, (" \t", None))),
                         {"items": [{"id": " \t", "value": None}], "evicted": []})

    def test_malformed_payloads_raise_value_error_at_both_seams(self):
        invalid = [None, [], (), "", 0, True, {}, {"capacity": 1},
                   {"events": []}]
        invalid += [{"capacity": value, "events": []}
                    for value in (True, False, -1, 1.0, "1", None, [], {})]
        invalid += [{"capacity": 1, "events": value}
                    for value in (None, {}, (), "", 1, True)]
        invalid += [{"capacity": 1, "events": [event]}
                    for event in (None, [], (), "", 1, {}, {"id": "a"},
                                  {"value": 1}, {"id": "", "value": 1},
                                  {"id": None, "value": 1},
                                  {"id": 1, "value": 1},
                                  {"id": True, "value": 1})]
        for data in invalid:
            for seam in (process, service.handle):
                with self.subTest(data=data, seam=seam.__name__):
                    before = copy.deepcopy(data)
                    with self.assertRaises(ValueError):
                        seam(data)
                    self.assertEqual(data, before)

    def test_non_json_values_are_rejected(self):
        for value in (object(), (1, 2), {1, 2}, {1: "bad key"},
                      float("inf"), float("nan"), [object()]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    process(payload(1, ("a", value)))
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaises(ValueError):
            process(payload(0, ("a", cyclic)))
        self.assertIs(cyclic[0], cyclic)

    def test_inputs_unchanged_on_success_and_late_failure(self):
        data = payload(1, ("a", {"nested": [1, None]}), ("a", [2]), ("b", 3))
        before = copy.deepcopy(data)
        process(data)
        service.handle(data)
        self.assertEqual(data, before)
        data["events"].append({"id": "bad"})
        before = copy.deepcopy(data)
        for seam in (process, service.handle):
            with self.assertRaises(ValueError):
                seam(data)
            self.assertEqual(data, before)

    def test_nested_results_are_independent_of_input(self):
        data = payload(1, ("a", {"nested": [1]}))
        result = process(data)
        result["items"][0]["value"]["nested"].append(2)
        self.assertEqual(data["events"][0]["value"], {"nested": [1]})


class Batch(unittest.TestCase):
    def test_batch_returns_results_in_order_without_mutation(self):
        data = [payload(1, ("a", 1), ("b", 2)), payload(0, ("c", None)),
                payload(2, ("d", [1]))]
        before = copy.deepcopy(data)
        self.assertEqual(service.batch(data), [
            {"items": [{"id": "b", "value": 2}], "evicted": ["a"]},
            {"items": [], "evicted": ["c"]},
            {"items": [{"id": "d", "value": [1]}], "evicted": []}])
        self.assertEqual(data, before)
        self.assertEqual(service.batch([]), [])

    def test_invalid_batch_and_invalid_members(self):
        for data in (None, {}, (), "", 1, [None],
                     [payload(1, ("a", {"nested": [1]})), payload(True)],
                     [payload(0), {"capacity": 1, "events": [{"id": "bad"}]}]):
            with self.subTest(data=data):
                before = copy.deepcopy(data)
                with self.assertRaises(ValueError):
                    service.batch(data)
                self.assertEqual(data, before)


class Cli(unittest.TestCase):
    def run_cli(self, data="", *args):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=data, cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_cli_fifo_result(self):
        data = payload(2, ("a", 1), ("b", None), ("a", 3), ("æ", [True]))
        result = self.run_cli(json.dumps(data))
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(json.loads(result.stdout), {
            "items": [{"id": "b", "value": None}, {"id": "æ", "value": [True]}],
            "evicted": ["a"]})

    def test_cli_rejects_invalid_inputs(self):
        for data in ("{", "null", '{"capacity": true, "events": []}',
                     '{"capacity": 0, "events": [{"id": "a"}]}'):
            with self.subTest(data=data):
                result = self.run_cli(data)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_keep_exact_behavior(self):
        for args in (("--unknown",), ("--version", "extra"), ("extra",)):
            with self.subTest(args=args):
                result = self.run_cli("invalid json", *args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

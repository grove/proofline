import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
import service


def record(identifier, value):
    return {"id": identifier, "value": value}


class CacheTests(unittest.TestCase):
    def test_update_preserves_position_and_latest_value(self):
        self.assertEqual(
            process({"capacity": 3, "events": [record("a", 1), record("b", 2),
                                                record("a", 3), record("c", 4)]}),
            {"items": [record("a", 3), record("b", 2), record("c", 4)],
             "evicted": []},
        )

    def test_updates_do_not_evict_at_capacity(self):
        self.assertEqual(
            process({"capacity": 1, "events": [record("a", 1), record("a", None)]}),
            {"items": [record("a", None)], "evicted": []},
        )

    def test_reinsertions_and_repeated_evictions(self):
        self.assertEqual(
            process({"capacity": 2, "events": [record("a", 1), record("b", 2),
                                                record("c", 3), record("a", 4),
                                                record("d", 5), record("e", 6)]}),
            {"items": [record("d", 5), record("e", 6)],
             "evicted": ["a", "b", "c", "a"]},
        )

    def test_zero_capacity_evicts_every_event(self):
        self.assertEqual(
            process({"capacity": 0, "events": [record("a", 1), record("a", 2),
                                                record("b", None), record("a", 3)]}),
            {"items": [], "evicted": ["a", "a", "b", "a"]},
        )

    def test_empty_events(self):
        for capacity in (0, 1, 100):
            with self.subTest(capacity=capacity):
                self.assertEqual(process({"capacity": capacity, "events": []}),
                                 {"items": [], "evicted": []})

    def test_json_values_extra_keys_and_nonmutation(self):
        values = [None, False, True, 0, -2, 1.25, "雪", [], {},
                  {"nested": [None, {"flag": False, "text": "hello"}]}]
        payload = {
            "capacity": len(values),
            "events": [{**record(str(i), value), "ignored": {"extra": [1]}}
                       for i, value in enumerate(values)],
            "extra": ["allowed"],
        }
        before = copy.deepcopy(payload)
        expected = {"items": [record(str(i), value) for i, value in enumerate(values)],
                    "evicted": []}
        for entry in (process, service.handle):
            with self.subTest(entry=entry.__name__):
                self.assertEqual(entry(payload), expected)
                self.assertEqual(payload, before)

    def test_whitespace_and_unicode_ids_are_nonempty(self):
        self.assertEqual(
            process({"capacity": 2, "events": [record(" ", None), record("雪", False)]}),
            {"items": [record(" ", None), record("雪", False)], "evicted": []},
        )

    def test_invalid_payloads_raise_valueerror_without_mutation(self):
        payloads = [None, False, 1, "text", [], (), {}, {"capacity": 1},
                    {"events": []}]
        payloads += [{"capacity": capacity, "events": []}
                     for capacity in (True, False, -1, 1.0, "1", None, [], {})]
        payloads += [{"capacity": 1, "events": events}
                     for events in (None, {}, (), "events", 1, False)]
        for payload in payloads:
            before = copy.deepcopy(payload)
            for entry in (process, service.handle):
                with self.subTest(payload=payload, entry=entry.__name__):
                    with self.assertRaises(ValueError):
                        entry(payload)
                    self.assertEqual(payload, before)

    def test_invalid_events_after_valid_event_do_not_mutate_input(self):
        invalid = [None, False, 1, "event", [], (), {}, {"id": "a"},
                   {"value": None}]
        invalid += [record(identifier, None) for identifier in
                    (None, False, 1, [], {}, "")]
        for event in invalid:
            for capacity in (0, 2):
                payload = {"capacity": capacity,
                           "events": [record("valid", {"nested": [1, None]}), event]}
                before = copy.deepcopy(payload)
                for entry in (process, service.handle):
                    with self.subTest(event=event, capacity=capacity, entry=entry.__name__):
                        with self.assertRaises(ValueError):
                            entry(payload)
                        self.assertEqual(payload, before)

    def test_non_json_values_are_rejected(self):
        for value in (object(), {1, 2}, (1, 2), float("nan"), float("inf"),
                      {1: "not a JSON key"}, {"nested": [object()]}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    process({"capacity": 1, "events": [record("a", value)]})

    def test_circular_values_raise_valueerror_without_modification(self):
        value = []
        value.append(value)
        payload = {"capacity": 1, "events": [record("a", value)]}
        with self.assertRaises(ValueError):
            process(payload)
        self.assertEqual(len(value), 1)
        self.assertIs(value[0], value)

    def test_shared_value_containers_are_allowed(self):
        shared = [None]
        value = {"a": shared, "b": shared}
        self.assertEqual(process({"capacity": 1, "events": [record("a", value)]}),
                         {"items": [record("a", {"a": [None], "b": [None]})],
                          "evicted": []})


class BatchTests(unittest.TestCase):
    def test_empty_batch(self):
        self.assertEqual(service.batch([]), [])

    def test_batch_preserves_order_and_inputs(self):
        payloads = [
            {"capacity": 0, "events": [record("a", None), record("a", 2)]},
            {"capacity": 2, "events": [record("a", {"nested": [1]}),
                                       record("b", 2), record("a", 3)]},
            {"capacity": 1, "events": [record("c", 1), record("d", 2)]},
        ]
        before = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [
            {"items": [], "evicted": ["a", "a"]},
            {"items": [record("a", 3), record("b", 2)], "evicted": []},
            {"items": [record("d", 2)], "evicted": ["c"]},
        ])
        self.assertEqual(payloads, before)

    def test_non_list_batch_is_rejected(self):
        for payloads in (None, {}, (), "", 1, False, iter([])):
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    service.batch(payloads)

    def test_invalid_member_does_not_mutate_any_input(self):
        valid = {"capacity": 1, "events": [record("a", {"nested": [None]})]}
        for invalid in (None, [], {}, {"capacity": True, "events": []},
                        {"capacity": 1, "events": [record("b", 1), {"id": "c"}]}):
            payloads = [valid, invalid, valid]
            before = copy.deepcopy(payloads)
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    service.batch(payloads)
                self.assertEqual(payloads, before)


class CliTests(unittest.TestCase):
    def run_cli(self, text="", arguments=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *arguments],
                              cwd=repo, input=text, capture_output=True,
                              text=True, timeout=5)

    def test_cli_cache_result(self):
        payload = {"capacity": 2, "events": [record("雪", None), record("b", 2),
                                              record("雪", {"new": [False]}),
                                              record("c", 4)]}
        result = self.run_cli(json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout),
                         {"items": [record("b", 2), record("c", 4)], "evicted": ["雪"]})

    def test_cli_zero_capacity(self):
        result = self.run_cli(json.dumps({"capacity": 0,
                                        "events": [record("a", None), record("a", 2)]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"items": [], "evicted": ["a", "a"]})

    def test_cli_invalid_requests(self):
        for text in ("not json", "null", '{"capacity": true, "events": []}',
                     '{"capacity": 0, "events": [{"id": "a"}]}'):
            with self.subTest(text=text):
                result = self.run_cli(text)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_exact_response(self):
        for arguments in (("--unknown",), ("--version", "extra"), ("--help",)):
            with self.subTest(arguments=arguments):
                result = self.run_cli(arguments=arguments)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

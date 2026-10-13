import copy
import itertools
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class DependencyOrder(unittest.TestCase):
    def test_ready_nodes_use_original_position_at_every_step(self):
        payload = {"nodes": ["z", "a", "b", "c"],
                   "edges": [["a", "z"], ["z", "b"]]}
        for entry in (app.process, service.handle):
            with self.subTest(entry=entry.__name__):
                self.assertEqual(entry(payload), {"order": ["a", "z", "b", "c"]})

    def test_duplicates_extra_keys_and_input_preservation(self):
        payload = {"nodes": ["later", "first", "free"],
                   "edges": [["first", "later"], ["first", "later"]],
                   "extra": {"nested": [1, 2]}}
        original = copy.deepcopy(payload)
        self.assertEqual(app.process(payload), {"order": ["first", "later", "free"]})
        self.assertEqual(payload, original)

    def test_empty_and_non_ascii_names(self):
        self.assertEqual(app.process({"nodes": [], "edges": []}), {"order": []})
        self.assertEqual(app.process({"nodes": ["雪", " ", "é"], "edges": []}),
                         {"order": ["雪", " ", "é"]})

    def test_invalid_records_raise_value_error_without_mutation(self):
        invalid = [
            None, False, 1, "record", [], {},
            {"nodes": []}, {"edges": []},
            {"nodes": None, "edges": []},
            {"nodes": "a", "edges": []},
            {"nodes": ("a",), "edges": []},
            {"nodes": [], "edges": None},
            {"nodes": [], "edges": {}},
            {"nodes": [], "edges": ()},
            {"nodes": [""], "edges": []},
            {"nodes": [1], "edges": []},
            {"nodes": [True], "edges": []},
            {"nodes": [[]], "edges": []},
            {"nodes": ["a", "a"], "edges": []},
            {"nodes": ["a", "b"], "edges": [None]},
            {"nodes": ["a", "b"], "edges": ["ab"]},
            {"nodes": ["a", "b"], "edges": [("a", "b")]},
            {"nodes": ["a", "b"], "edges": [[]]},
            {"nodes": ["a", "b"], "edges": [["a"]]},
            {"nodes": ["a", "b"], "edges": [["a", "b", "a"]]},
            {"nodes": ["a", "b"], "edges": [[[], "b"]]},
            {"nodes": ["a", "b"], "edges": [["a", {}]]},
            {"nodes": ["a", "b"], "edges": [["a", "missing"]]},
            {"nodes": [], "edges": [["a", "b"]]},
            {"nodes": ["a"], "edges": [["a", "a"]]},
            {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]},
            {"nodes": ["free", "a", "b"],
             "edges": [["a", "b"], ["b", "a"]]},
            {"nodes": ["free", "a", "b", "c"],
             "edges": [["a", "b"], ["b", "c"], ["c", "a"]]},
        ]
        for payload in invalid:
            original = copy.deepcopy(payload)
            for entry in (app.process, service.handle):
                with self.subTest(payload=payload, entry=entry.__name__):
                    with self.assertRaises(ValueError):
                        entry(payload)
                    self.assertEqual(payload, original)

    def test_all_three_node_graphs_against_scan_reference(self):
        # A separate oracle repeatedly scans the original list for a ready node.
        # All directed graphs and node permutations exercise both cycles and ties.
        for nodes in itertools.permutations(["z", "a", "m"]):
            possible_edges = list(itertools.permutations(nodes, 2))
            for mask in range(1 << len(possible_edges)):
                edges = [list(edge) for i, edge in enumerate(possible_edges)
                         if mask & (1 << i)]
                emitted = []
                while len(emitted) < len(nodes):
                    ready = next((node for node in nodes if node not in emitted
                                  and all(before in emitted for before, after in edges
                                          if after == node)), None)
                    if ready is None:
                        break
                    emitted.append(ready)
                payload = {"nodes": list(nodes), "edges": edges}
                with self.subTest(payload=payload):
                    if len(emitted) != len(nodes):
                        with self.assertRaises(ValueError):
                            app.process(payload)
                    else:
                        self.assertEqual(app.process(payload), {"order": emitted})


class Batch(unittest.TestCase):
    def test_order_empty_and_input_preservation(self):
        payloads = [{"nodes": ["z", "a"], "edges": []},
                    {"nodes": [], "edges": []},
                    {"nodes": ["b", "a"], "edges": [["a", "b"]]}]
        original = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads),
                         [{"order": ["z", "a"]}, {"order": []}, {"order": ["a", "b"]}])
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_rejects_non_list(self):
        for payloads in (None, {}, "records", (), 1, True):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_member_raises_without_mutation(self):
        valid = {"nodes": ["z", "a"], "edges": []}
        invalid = {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]}
        for payloads in ([invalid, valid], [valid, invalid], [valid, None]):
            original = copy.deepcopy(payloads)
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)
            self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, *args, stdin=""):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, capture_output=True, text=True,
                              cwd=repo, timeout=5)

    def test_json_order(self):
        result = self.run_cli(stdin=json.dumps({"nodes": ["雪", "z", "a"],
                                               "edges": [["z", "雪"]]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"order": ["z", "雪", "a"]})
        self.assertIn("雪", result.stdout)

    def test_invalid_input(self):
        for stdin in ('{"nodes": ["a"], "edges": [["a", "a"]]}',
                      '{"nodes": []}', 'null', '{invalid json'):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin=stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra"), ("value",)):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

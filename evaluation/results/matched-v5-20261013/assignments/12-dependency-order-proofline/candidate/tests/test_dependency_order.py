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
    def assert_unchanged(self, payload, expected=None):
        original = copy.deepcopy(payload)
        for handler in (app.process, service.handle):
            with self.subTest(handler=handler.__name__):
                if expected is None:
                    with self.assertRaises(ValueError):
                        handler(payload)
                else:
                    self.assertEqual(handler(payload), {"order": expected})
                self.assertEqual(payload, original)

    def test_newly_ready_node_takes_priority(self):
        self.assert_unchanged(
            {"nodes": ["z", "a", "b", "c"],
             "edges": [["a", "z"], ["z", "c"], ["b", "c"]]},
            ["a", "z", "b", "c"],
        )

    def test_empty_and_extra_keys(self):
        self.assert_unchanged({"nodes": [], "edges": [], "extra": [1]}, [])
        self.assert_unchanged({"nodes": ["β", " "], "edges": []}, ["β", " "])

    def test_repeated_edges(self):
        self.assert_unchanged(
            {"nodes": ["after", "before"],
             "edges": [["before", "after"]] * 3},
            ["before", "after"],
        )

    def test_malformed_records(self):
        invalid = [
            None, [], "record", 1,
            {}, {"nodes": []}, {"edges": []},
            {"nodes": (), "edges": []},
            {"nodes": [], "edges": ()},
            {"nodes": "a", "edges": []},
        ]
        for nodes in ([""], [1], [None], [[]], [{}], [True], ["a", "a"]):
            invalid.append({"nodes": nodes, "edges": []})
        for edge in (None, "ab", [], ["a"], ["a", "b", "a"],
                     ("a", "b"), [[], "b"], ["a", {}], [1, "b"],
                     ["missing", "b"], ["a", "missing"], ["a", "a"]):
            invalid.append({"nodes": ["a", "b"], "edges": [edge]})
        invalid.append({"nodes": [], "edges": [["a", "b"]]})
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assert_unchanged(payload)

    def test_cycles_including_disconnected_cycle(self):
        for payload in (
            {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]},
            {"nodes": ["free", "a", "b", "c"],
             "edges": [["a", "b"], ["b", "c"], ["c", "a"]]},
        ):
            self.assert_unchanged(payload)

    def test_all_three_node_graphs_against_valid_permutations(self):
        # The lexicographically smallest valid permutation of original indexes
        # independently specifies the requested priority at each step.
        nodes = ["z", "a", "m"]
        pairs = list(itertools.permutations(range(3), 2))
        for mask in range(1 << len(pairs)):
            edges = [pair for bit, pair in enumerate(pairs) if mask & (1 << bit)]
            valid = []
            for permutation in itertools.permutations(range(3)):
                positions = {node: index for index, node in enumerate(permutation)}
                if all(positions[a] < positions[b] for a, b in edges):
                    valid.append(permutation)
            payload = {"nodes": nodes,
                       "edges": [[nodes[a], nodes[b]] for a, b in reversed(edges)]}
            with self.subTest(edges=edges):
                if valid:
                    expected = [nodes[index] for index in min(valid)]
                    self.assert_unchanged(payload, expected)
                else:
                    self.assert_unchanged(payload)


class Batch(unittest.TestCase):
    def test_results_in_input_order(self):
        payloads = [{"nodes": ["z", "a"], "edges": []},
                    {"nodes": [], "edges": []}]
        original = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads), [{"order": ["z", "a"]},
                                                   {"order": []}])
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_rejects_invalid_input_without_mutation(self):
        good = {"nodes": ["a"], "edges": []}
        bad = {"nodes": ["a"], "edges": [["a", "a"]]}
        for payloads in (None, {}, (), "records", [good, bad], [bad, good], [good, None]):
            original = copy.deepcopy(payloads)
            with self.subTest(payloads=payloads):
                with self.assertRaises(ValueError):
                    service.batch(payloads)
                self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, stdin="", args=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_json_input_output(self):
        payload = {"nodes": ["β", "a", "z"], "edges": [["a", "β"]]}
        result = self.run_cli(json.dumps(payload))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, '{"order": ["a", "β", "z"]}\n', ""))

    def test_invalid_records_and_json(self):
        for stdin in ('{"nodes":["a"],"edges":[["a","a"]]}',
                      '{"nodes":[],"edges":[["a","b"]]}', 'null', '{'):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra")):
            with self.subTest(args=args):
                result = self.run_cli(args=args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest

import app
import service


class DependencyOrder(unittest.TestCase):
    def test_valid_graphs_at_both_entry_points(self):
        cases = [
            ({"nodes": [], "edges": []}, []),
            ({"nodes": ["z", "a"], "edges": []}, ["z", "a"]),
            ({"nodes": ["a", "b", "c"], "edges": [["b", "a"]]},
             ["b", "a", "c"]),
            ({"nodes": ["a", "b", "c", "d"],
              "edges": [["b", "a"], ["c", "b"]]}, ["c", "b", "a", "d"]),
            ({"nodes": ["end", "left", "right", "start"],
              "edges": [["start", "left"], ["start", "right"],
                        ["left", "end"], ["right", "end"]]},
             ["start", "left", "right", "end"]),
            ({"nodes": ["a", "b", "c"],
              "edges": [["b", "a"], ["b", "a"], ["b", "a"]]},
             ["b", "a", "c"]),
            ({"nodes": ["β", " ", "\t", "Z"], "edges": [],
              "extra": {"nested": [1, 2]}}, ["β", " ", "\t", "Z"]),
        ]
        for entry in (app.process, service.handle):
            for payload, expected in cases:
                with self.subTest(entry=entry.__name__, payload=payload):
                    original = copy.deepcopy(payload)
                    self.assertEqual(entry(payload), {"order": expected})
                    self.assertEqual(payload, original)

    def test_invalid_graphs_raise_value_error_without_mutation(self):
        cases = [
            None, True, 1, "graph", [], (), {},
            {"nodes": []}, {"edges": []},
            {"nodes": (), "edges": []},
            {"nodes": [], "edges": ()},
            {"nodes": "ab", "edges": []},
            {"nodes": [], "edges": {}},
            {"nodes": [""], "edges": []},
            {"nodes": ["a", "a"], "edges": []},
            {"nodes": [None], "edges": []},
            {"nodes": [1], "edges": []},
            {"nodes": [True], "edges": []},
            {"nodes": [[]], "edges": []},
            {"nodes": [{}], "edges": []},
            {"nodes": [], "edges": [["a", "b"]]},
            {"nodes": ["a", "b"], "edges": [None]},
            {"nodes": ["a", "b"], "edges": ["ab"]},
            {"nodes": ["a", "b"], "edges": [("a", "b")]},
            {"nodes": ["a", "b"], "edges": [[]]},
            {"nodes": ["a", "b"], "edges": [["a"]]},
            {"nodes": ["a", "b"], "edges": [["a", "b", "a"]]},
            {"nodes": ["a", "b"], "edges": [["a", "unknown"]]},
            {"nodes": ["a", "b"], "edges": [["unknown", "a"]]},
            {"nodes": ["a", "b"], "edges": [[[], "a"]]},
            {"nodes": ["a", "b"], "edges": [["a", {}]]},
            {"nodes": ["a", "b"], "edges": [[1, "b"]]},
            {"nodes": ["a"], "edges": [["a", "a"]]},
            {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]},
            {"nodes": ["free", "a", "b"],
             "edges": [["a", "b"], ["b", "a"]]},
            {"nodes": ["a", "b", "c", "free"],
             "edges": [["a", "b"], ["b", "c"], ["c", "a"]]},
        ]
        for entry in (app.process, service.handle):
            for payload in cases:
                with self.subTest(entry=entry.__name__, payload=payload):
                    original = copy.deepcopy(payload)
                    with self.assertRaises(ValueError):
                        entry(payload)
                    self.assertEqual(payload, original)

    def test_every_four_node_graph_against_permutation_oracle(self):
        # Permutations are ordered by original node position. The first valid
        # one is the independently expected stable order; none means a cycle.
        nodes = ["z", "a", "β", "x"]
        possible_edges = list(itertools.permutations(range(4), 2))
        permutations = list(itertools.permutations(range(4)))
        rank_maps = [{node: rank for rank, node in enumerate(order)}
                     for order in permutations]
        for mask in range(1 << len(possible_edges)):
            edges = [edge for bit, edge in enumerate(possible_edges)
                     if mask & (1 << bit)]
            expected = next((order for order, ranks in zip(permutations, rank_maps)
                             if all(ranks[a] < ranks[b] for a, b in edges)), None)
            payload = {"nodes": nodes,
                       "edges": [[nodes[a], nodes[b]] for a, b in edges]}
            with self.subTest(mask=mask):
                if expected is None:
                    with self.assertRaises(ValueError):
                        app.process(payload)
                else:
                    self.assertEqual(app.process(payload),
                                     {"order": [nodes[i] for i in expected]})

    def test_batch_order_and_empty_batch(self):
        payloads = [{"nodes": ["z", "a"], "edges": []},
                    {"nodes": ["a", "b", "c"], "edges": [["b", "a"]]},
                    {"nodes": [], "edges": []}]
        original = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads),
                         [{"order": ["z", "a"]},
                          {"order": ["b", "a", "c"]}, {"order": []}])
        self.assertEqual(payloads, original)
        self.assertEqual(service.batch([]), [])

    def test_invalid_batch_does_not_mutate_any_member(self):
        valid = {"nodes": ["a", "b"], "edges": [["b", "a"]]}
        cyclic = {"nodes": ["free", "a", "b"],
                  "edges": [["a", "b"], ["b", "a"]]}
        for payloads in (None, {}, "[]", (), [valid, None],
                         [cyclic, valid], [valid, cyclic], [valid, {}]):
            with self.subTest(payloads=payloads):
                original = copy.deepcopy(payloads)
                with self.assertRaises(ValueError):
                    service.batch(payloads)
                self.assertEqual(payloads, original)

    def test_result_does_not_alias_input_nodes(self):
        payload = {"nodes": ["z", "a"], "edges": []}
        for entry in (app.process, service.handle):
            entry(payload)["order"].append("new")
            self.assertEqual(payload["nodes"], ["z", "a"])
        service.batch([payload])[0]["order"].append("new")
        self.assertEqual(payload["nodes"], ["z", "a"])


class CliBehavior(unittest.TestCase):
    def run_cli(self, stdin="", args=()):
        repo = Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, capture_output=True, text=True,
                              cwd=repo, timeout=5)

    def test_json_order(self):
        result = self.run_cli(json.dumps({"nodes": ["a", "b", "β"],
                                         "edges": [["b", "a"]]}))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, '{"order": ["b", "a", "β"]}\n', ""))

    def test_invalid_json_and_graph(self):
        for stdin in ("not JSON", "null", "[]", "{}",
                      '{"nodes": ["a"], "edges": [["a", "a"]]}',
                      '{"nodes": ["free", "a", "b"], '
                      '"edges": [["a", "b"], ["b", "a"]]}'):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for args in (("--unknown",), ("--version", "extra"), ("input.json",)):
            with self.subTest(args=args):
                result = self.run_cli("not JSON", args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

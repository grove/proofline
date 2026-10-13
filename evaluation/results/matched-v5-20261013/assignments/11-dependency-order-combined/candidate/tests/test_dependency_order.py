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
    def test_orders(self):
        cases = [
            ({"nodes": [], "edges": []}, []),
            ({"nodes": ["z", "a", "m"], "edges": []}, ["z", "a", "m"]),
            # Newly available a must jump ahead of already available c.
            ({"nodes": ["a", "b", "c"], "edges": [["b", "a"]]},
             ["b", "a", "c"]),
            ({"nodes": ["end", "left", "right", "start"],
              "edges": [["start", "left"], ["start", "right"],
                        ["left", "end"], ["right", "end"]]},
             ["start", "left", "right", "end"]),
            ({"nodes": ["end", "start"],
              "edges": [["start", "end"], ["start", "end"]]},
             ["start", "end"]),
            ({"nodes": [" ", "\t", "é", "Z"], "edges": [],
              "metadata": {"arbitrary": [None, 2]}}, [" ", "\t", "é", "Z"]),
        ]
        for payload, order in cases:
            for process in (app.process, service.handle):
                with self.subTest(payload=payload, process=process.__name__):
                    original = copy.deepcopy(payload)
                    self.assertEqual(process(payload), {"order": order})
                    self.assertEqual(payload, original)

    def test_invalid_records_do_not_mutate(self):
        invalid = [
            None, True, 1, "graph", [], (), {},
            {"nodes": []}, {"edges": []},
            {"nodes": None, "edges": []},
            {"nodes": "ab", "edges": []},
            {"nodes": (), "edges": []},
            {"nodes": [], "edges": None},
            {"nodes": [], "edges": {}},
            {"nodes": [], "edges": ()},
            {"nodes": [""], "edges": []},
            {"nodes": ["a", "a"], "edges": []},
            *({"nodes": ["a", name], "edges": []}
              for name in (None, False, 3, [], {})),
            *({"nodes": ["a", "b"], "edges": [edge]}
              for edge in (None, 1, "ab", {}, ("a", "b"), [], ["a"],
                           ["a", "b", "a"], ["missing", "a"],
                           ["a", "missing"], [[], "a"], ["a", {}],
                           [1, "a"], ["a", None], ["a", "a"])),
            {"nodes": [], "edges": [["a", "b"]]},
            {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]},
            # An unrelated root cannot hide a disconnected cycle.
            {"nodes": ["root", "a", "b", "leaf"],
             "edges": [["root", "leaf"], ["a", "b"], ["b", "a"]]},
        ]
        for payload in invalid:
            for process in (app.process, service.handle):
                with self.subTest(payload=payload, process=process.__name__):
                    original = copy.deepcopy(payload)
                    with self.assertRaises(ValueError):
                        process(payload)
                    self.assertEqual(payload, original)

    def test_all_four_node_graphs_against_permutation_oracle(self):
        # Enumerate legal full orders independently of the implementation.
        # Permutations come in original-index lexicographic order, so the
        # first legal one encodes the required earliest-eligible choice.
        nodes = ["z", "a", "m", "b"]
        possible_edges = list(itertools.permutations(range(4), 2))
        permutations = list(itertools.permutations(range(4)))
        ranks = [{node: rank for rank, node in enumerate(order)}
                 for order in permutations]
        for mask in range(1 << len(possible_edges)):
            edges = [edge for bit, edge in enumerate(possible_edges)
                     if mask & (1 << bit)]
            expected = next((order for order, rank in zip(permutations, ranks)
                             if all(rank[a] < rank[b] for a, b in edges)), None)
            payload = {"nodes": nodes,
                       "edges": [[nodes[a], nodes[b]] for a, b in edges]}
            with self.subTest(mask=mask):
                if expected is None:
                    with self.assertRaises(ValueError):
                        app.process(payload)
                else:
                    self.assertEqual(app.process(payload),
                                     {"order": [nodes[i] for i in expected]})

    def test_long_chain(self):
        nodes = [str(i) for i in range(2000)]
        payload = {"nodes": nodes,
                   "edges": [[nodes[i + 1], nodes[i]] for i in range(1999)]}
        self.assertEqual(app.process(payload), {"order": nodes[::-1]})


class Batch(unittest.TestCase):
    def test_empty_and_ordered_batch(self):
        self.assertEqual(service.batch([]), [])
        payloads = [
            {"nodes": ["a", "b", "c"], "edges": [["b", "a"]]},
            {"nodes": [], "edges": []},
            {"nodes": ["z", "a"], "edges": []},
        ]
        original = copy.deepcopy(payloads)
        self.assertEqual(service.batch(payloads),
                         [{"order": ["b", "a", "c"]}, {"order": []},
                          {"order": ["z", "a"]}])
        self.assertEqual(payloads, original)

    def test_non_list(self):
        for payloads in (None, {}, (), "batch", 1, False):
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                service.batch(payloads)

    def test_invalid_members_preserve_whole_batch(self):
        valid = {"nodes": ["z", "a"], "edges": [], "extra": [1, 2]}
        for invalid in (None, [], {}, {"nodes": ["a"], "edges": [["a", "a"]]}):
            for payloads in ([invalid, valid], [valid, invalid]):
                with self.subTest(payloads=payloads):
                    original = copy.deepcopy(payloads)
                    with self.assertRaises(ValueError):
                        service.batch(payloads)
                    self.assertEqual(payloads, original)


class CLI(unittest.TestCase):
    def run_cli(self, args=(), stdin=""):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *args],
                              input=stdin, cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_graph_input(self):
        payload = {"nodes": ["é", "b", "c"], "edges": [["b", "é"]]}
        result = self.run_cli(stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"order": ["b", "é", "c"]})

    def test_invalid_graph_and_json(self):
        for stdin in ('{"nodes": ["a"], "edges": [["a", "a"]]}',
                      '{"nodes": ["root", "a", "b"],'
                      ' "edges": [["a", "b"], ["b", "a"]]}',
                      '{}', 'null', '{'):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin=stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_exact_unsupported_argument_behavior(self):
        for args in (["--other"], ["--version", "extra"], ["--version", "--version"]):
            with self.subTest(args=args):
                result = self.run_cli(args, stdin="invalid JSON")
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))


if __name__ == "__main__":
    unittest.main()

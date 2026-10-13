import copy
import json
import pathlib
import random
import subprocess
import sys
import unittest

import app
import service


class IntervalUnion(unittest.TestCase):
    def test_merge_unsorted_overlapping_touching_and_nested_intervals(self):
        payload = {"intervals": [[8, 10], [2, 5], [4, 8], [3, 4],
                                 [12, 15], [2, 5], [10, 10]]}
        original = copy.deepcopy(payload)
        self.assertEqual(app.process(payload),
                         {"segments": [[2, 10], [12, 15]], "covered": 11})
        self.assertEqual(payload, original)

    def test_empty_and_zero_length_intervals(self):
        for intervals in ([], [[0, 0], [100, 100], [200, 200]]):
            with self.subTest(intervals=intervals):
                self.assertEqual(app.process({"intervals": intervals}),
                                 {"segments": [], "covered": 0})

    def test_coordinate_boundaries_and_service(self):
        self.assertEqual(service.handle({"intervals": [[100, 200], [0, 100]]}),
                         {"segments": [[0, 200]], "covered": 200})

    def test_malformed_payloads(self):
        for payload in (None, [], "intervals", 5, {}, {"intervals": None},
                        {"intervals": {}}, {"intervals": "0,1"},
                        {"intervals": ((0, 1),)}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    app.process(payload)

    def test_malformed_intervals(self):
        for interval in (None, 0, "01", {}, [], [1], [1, 2, 3], (0, 1),
                         [False, 1], [0, True], [False, False], [0.0, 1],
                         [0, 1.0], ["0", 1], [0, None], [-1, 0],
                         [0, 201], [201, 201], [-1, -1], [2, 1]):
            with self.subTest(interval=interval):
                with self.assertRaises(ValueError):
                    app.process({"intervals": [[0, 200], interval]})

    def test_random_unions_against_integer_coverage(self):
        rng = random.Random(0)
        for _ in range(200):
            intervals = [sorted([rng.randrange(201), rng.randrange(201)])
                         for _ in range(rng.randrange(30))]
            covered = {point for start, end in intervals
                       for point in range(start, end)}
            expected_segments = []
            for point in sorted(covered):
                if expected_segments and expected_segments[-1][1] == point:
                    expected_segments[-1][1] = point + 1
                else:
                    expected_segments.append([point, point + 1])
            self.assertEqual(app.process({"intervals": intervals}),
                             {"segments": expected_segments,
                              "covered": len(covered)})

    def test_json_cli(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py")],
                                cwd=repo, input='{"intervals": [[3, 5], [0, 3]]}',
                                capture_output=True, text=True, timeout=5)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(json.loads(result.stdout),
                         {"segments": [[0, 5]], "covered": 5})

    def test_invalid_json_cli_input(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py")],
                                cwd=repo, input='{"intervals": [[true, 2]]}',
                                capture_output=True, text=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith("ERROR: "))

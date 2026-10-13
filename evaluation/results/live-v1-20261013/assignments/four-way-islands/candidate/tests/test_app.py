import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Islands(unittest.TestCase):
    def test_components(self):
        cases = [
            (["."], []),
            (["#"], [1]),
            (["...", "..."], []),
            (["###", "###"], [6]),
            (["#.", ".#"], [1, 1]),
            (["#.#", ".#.", "#.#"], [1, 1, 1, 1, 1]),
            (["#.##.###"], [3, 2, 1]),
            (["#", "#", ".", "#"], [2, 1]),
            (["###", "#.#", "###"], [8]),
            (["##..#", "#...#", "..#.#", "..##."], [3, 3, 3]),
        ]
        for grid, sizes in cases:
            with self.subTest(grid=grid):
                self.assertEqual(app.process({"grid": grid}),
                                 {"count": len(sizes), "sizes": sizes})

    def test_invalid_grids(self):
        invalid = [
            None, [], "#", 1, {}, [""], ["", ""],
            ["#", "##"], ["#", ""], ["#", None], [1],
            [["#"]], ["x"], ["# "], ["#\n"], ["＃"],
        ]
        for grid in invalid:
            with self.subTest(grid=grid):
                with self.assertRaises(ValueError):
                    app.process({"grid": grid})
        for payload in (None, [], "#", 1, {}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    app.process(payload)

    def test_payload_is_preserved(self):
        payload = {"grid": ["##.", ".##"], "metadata": {"id": 1}}
        original = copy.deepcopy(payload)
        self.assertEqual(app.process(payload), {"count": 1, "sizes": [4]})
        self.assertEqual(payload, original)
        self.assertEqual(app.process(payload), {"count": 1, "sizes": [4]})

    def test_large_component_without_recursion(self):
        self.assertEqual(app.process({"grid": ["#" * 5000]}),
                         {"count": 1, "sizes": [5000]})

    def test_service(self):
        self.assertEqual(service.handle({"grid": ["#.", ".#"]}),
                         {"count": 2, "sizes": [1, 1]})
        with self.assertRaises(ValueError):
            service.handle({"grid": []})

    def test_cli(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        for payload, expected in (
            ({"grid": ["#.", ".#"]}, {"count": 2, "sizes": [1, 1]}),
            ({"grid": []}, None),
        ):
            with self.subTest(payload=payload):
                result = subprocess.run(
                    [sys.executable, "-B", str(repo / "cli.py")],
                    cwd=repo, input=json.dumps(payload),
                    capture_output=True, text=True, timeout=5,
                )
                if expected is None:
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertTrue(result.stderr.startswith("ERROR: "))
                else:
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(json.loads(result.stdout), expected)
                    self.assertEqual(result.stderr, "")

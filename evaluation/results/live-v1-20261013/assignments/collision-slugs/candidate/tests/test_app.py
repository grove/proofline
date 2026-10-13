import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class Slugs(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(
            app.process({"titles": ["  Hello, WORLD!  ", "A___B / C", "123", "Café", "İ"]}),
            {"slugs": ["hello-world", "a-b-c", "123", "caf", "i"]},
        )

    def test_global_collisions_and_literal_suffixes(self):
        self.assertEqual(
            app.process({"titles": ["Name", "name-2", "NAME", "name-3", "name", "name-2"]}),
            {"slugs": ["name", "name-2", "name-3", "name-3-2", "name-4", "name-2-2"]},
        )

    def test_future_bases_are_not_reserved(self):
        self.assertEqual(
            app.process({"titles": ["x", "x", "x-2", "x", "x-2-2", "x-2"]}),
            {"slugs": ["x", "x-2", "x-2-2", "x-3", "x-2-2-2", "x-2-3"]},
        )

    def test_first_unused_suffix(self):
        self.assertEqual(
            app.process({"titles": ["x-3", "x-5", "x", "x", "x", "x"]}),
            {"slugs": ["x-3", "x-5", "x", "x-2", "x-4", "x-6"]},
        )

    def test_empty_list(self):
        self.assertEqual(app.process({"titles": []}), {"slugs": []})

    def test_invalid_payloads(self):
        invalid = [None, [], "titles", 1, {}, {"titles": None}, {"titles": "x"},
                   {"titles": ("x",)}, {"titles": {}}, {"titles": [None]},
                   {"titles": [1]}, {"titles": [True]}, {"titles": [[]]},
                   {"titles": [""]}, {"titles": [" -- ! "]}, {"titles": ["中文"]},
                   {"titles": ["valid", ""]}]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    app.process(payload)

    def test_no_mutation_or_cross_request_state(self):
        payload = {"titles": ["Same", "same", "same-2"]}
        original = copy.deepcopy(payload)
        expected = {"slugs": ["same", "same-2", "same-2-2"]}
        self.assertEqual(app.process(payload), expected)
        self.assertEqual(service.handle(payload), expected)
        self.assertEqual(payload, original)

    def test_cli_json_and_invalid_input(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        for payload, status in [({"titles": ["Hi!", "hi"]}, 0), ({"titles": [""]}, 2)]:
            with self.subTest(payload=payload):
                result = subprocess.run(
                    [sys.executable, "-B", str(repo / "cli.py")],
                    input=json.dumps(payload), cwd=repo, capture_output=True,
                    text=True, timeout=5,
                )
                self.assertEqual(result.returncode, status)
                if status == 0:
                    self.assertEqual(json.loads(result.stdout), {"slugs": ["hi", "hi-2"]})
                    self.assertEqual(result.stderr, "")
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertTrue(result.stderr.startswith("ERROR: "))

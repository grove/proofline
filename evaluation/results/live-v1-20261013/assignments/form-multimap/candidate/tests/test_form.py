import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class FormParsing(unittest.TestCase):
    def test_empty_segments_and_missing_values(self):
        self.assertEqual(app.process({"query": ""}), {"fields": {}})
        self.assertEqual(app.process({"query": "&&a&b=&a=last&&"}),
                         {"fields": {"a": ["", "last"], "b": [""]}})

    def test_first_equals_and_escaped_delimiters(self):
        self.assertEqual(app.process({"query": "a=b=c&x%26y=%3D%26%25"}),
                         {"fields": {"a": ["b=c"], "x&y": ["=&%"]}})

    def test_plus_and_percent_decoding_are_not_recursive(self):
        self.assertEqual(app.process({"query": "a+b=+%2B%2520"}),
                         {"fields": {"a b": [" +%20"]}})

    def test_unicode_and_equivalent_repeated_names(self):
        self.assertEqual(
            app.process({"query": "café=雪&caf%C3%A9=%E9%9B%AA&café=🙂%20ok"}),
            {"fields": {"café": ["雪", "雪", "🙂 ok"]}})

    def test_invalid_percent_escapes(self):
        for bad in ("%", "%0", "%GG", "% 0", "%+1", "%１0"):
            for query in (bad + "=value", "name=" + bad):
                with self.subTest(query=query), self.assertRaises(ValueError):
                    app.process({"query": query})

    def test_invalid_utf8(self):
        for bad in ("%FF", "%C3", "%C0%AF", "%ED%A0%80", "%F4%90%80%80",
                    "%80", "%C3é", "\ud800"):
            for query in (bad + "=value", "name=" + bad):
                with self.subTest(query=repr(query)), self.assertRaises(ValueError):
                    app.process({"query": query})

    def test_empty_names_rejected_but_spaces_allowed(self):
        for query in ("=value", "=", "a=1&&=2"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                app.process({"query": query})
        self.assertEqual(app.process({"query": "+=value"}),
                         {"fields": {" ": ["value"]}})

    def test_service_and_json_cli(self):
        payload = {"query": "a=1&a=2&雪=🙂"}
        expected = {"fields": {"a": ["1", "2"], "雪": ["🙂"]}}
        self.assertEqual(service.handle(payload), expected)
        repo = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py")],
                                input=json.dumps(payload), cwd=repo,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), expected)
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py")],
                                input=json.dumps({"query": "a=%FF"}), cwd=repo,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("ERROR: "))


if __name__ == "__main__":
    unittest.main()

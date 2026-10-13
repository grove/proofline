import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


def payload(**overrides):
    value = {
        "catalog": {"en": {"a": "English"}},
        "locales": ["en"],
        "keys": ["a"],
        "default": "en",
    }
    value.update(overrides)
    return value


class Resolution(unittest.TestCase):
    def test_per_key_order_and_all_truncation_levels(self):
        value = payload(
            catalog={
                "zh-Hant-TW": {"a": "exact"},
                "zh-Hant": {"a": "shadowed", "b": "script"},
                "zh": {"c": "language"},
                "fr-CA": {"b": "later exact", "d": "Canada"},
                "fr": {"e": "France"},
                "en": {"f": "default"},
            },
            locales=["zh-Hant-TW", "fr-CA"],
            keys=["a", "b", "c", "d", "e", "f", "missing", "a"],
        )
        self.assertEqual(app.process(value), {
            "texts": ["exact", "script", "language", "Canada", "France",
                      "default", None, "exact"]
        })

    def test_later_requested_locale_precedes_default(self):
        self.assertEqual(app.process(payload(
            catalog={"en": {"a": "default"}, "fr": {"a": "requested"}},
            locales=["missing-AA", "fr-CA"],
        )), {"texts": ["requested"]})

    def test_default_is_exact_only(self):
        value = payload(
            catalog={"en-US": {"a": "US"}, "en": {"b": "parent"}},
            locales=[], keys=["a", "b"], default="en-US",
        )
        self.assertEqual(app.process(value), {"texts": ["US", None]})
        value["locales"] = ["en-GB"]
        self.assertEqual(app.process(value), {"texts": ["US", "parent"]})

    def test_empty_string_is_a_hit_at_every_level(self):
        for locales, catalog in [
            (["fr-CA", "en"], {"fr-CA": {"a": ""}, "fr": {"a": "parent"},
                                "en": {"a": "default"}}),
            (["fr-CA", "en"], {"fr": {"a": ""}, "en": {"a": "default"}}),
            ([], {"en": {"a": ""}}),
        ]:
            with self.subTest(locales=locales, catalog=catalog):
                self.assertEqual(app.process(payload(locales=locales, catalog=catalog)),
                                 {"texts": [""]})

    def test_case_sensitive_locales_and_keys(self):
        value = payload(
            catalog={"FR": {"a": "uppercase locale"},
                     "fr": {"A": "uppercase key"}, "en": {"a": "fallback"}},
            locales=["fr"], keys=["a", "A", "missing"],
        )
        self.assertEqual(app.process(value), {"texts": ["fallback", "uppercase key", None]})

    def test_empty_containers(self):
        self.assertEqual(app.process(payload(catalog={}, locales=[], keys=[])),
                         {"texts": []})
        self.assertEqual(app.process(payload(catalog={})), {"texts": [None]})
        self.assertEqual(app.process(payload(catalog={"en": {}}, locales=[])),
                         {"texts": [None]})

    def test_unrestricted_nonempty_strings_and_extra_fields(self):
        value = payload(
            catalog={" x_1--": {" ": "exact"}, " x_1-": {"b": "parent"},
                     " x_1": {"c": "root"}, "-": {"d": "dash"},
                     " ": {"e": "space default"}},
            locales=[" x_1--", "-"], keys=[" ", "b", "c", "d", "e"],
            default=" ", extra={"anything": [None, 5]},
        )
        self.assertEqual(app.process(value), {
            "texts": ["exact", "parent", "root", "dash", "space default"]
        })


class ValidationAndPreservation(unittest.TestCase):
    def test_invalid_payloads_raise_valueerror_without_mutation(self):
        invalid = [None, [], "payload", 0, True]
        for field in ("catalog", "locales", "keys", "default"):
            value = payload()
            del value[field]
            invalid.append(value)
        for catalog in ([], None, "catalog", 3, {"": {}}, {1: {}},
                        {"en": []}, {"en": None}, {"en": {"": "text"}},
                        {"en": {1: "text"}}, {"en": {"a": None}},
                        {"en": {"a": False}}, {"en": {"a": []}},
                        {"en": {"a": 2}}, {"unused": {"a": {}}}):
            invalid.append(payload(catalog=catalog, keys=[]))
        for field in ("locales", "keys"):
            for value in (None, {}, "en", ("en",), [""], [1], [False], [None], [[]]):
                invalid.append(payload(**{field: value}))
        for default in (None, "", 1, False, [], {}):
            invalid.append(payload(default=default, keys=[]))
        for value in invalid:
            for api in (app.process, service.handle):
                with self.subTest(value=value, api=api.__name__):
                    before = copy.deepcopy(value)
                    with self.assertRaises(ValueError):
                        api(value)
                    self.assertEqual(value, before)

    def test_success_preserves_nested_input_for_all_entrypoints(self):
        value = payload(
            catalog={"fr": {"a": "", "b": "é"}, "en": {"c": "English"}},
            locales=["fr-CA"], keys=["a", "b", "c", "a", "missing"],
            extra={"nested": ["untouched"]},
        )
        before = copy.deepcopy(value)
        expected = {"texts": ["", "é", "English", "", None]}
        self.assertEqual(app.process(value), expected)
        self.assertEqual(service.handle(value), expected)
        self.assertEqual(service.batch([value, value]), [expected, expected])
        self.assertEqual(value, before)


class Batch(unittest.TestCase):
    def test_order_and_empty_batch(self):
        self.assertEqual(service.batch([]), [])
        self.assertEqual(service.batch([
            payload(), payload(catalog={}), payload(keys=[]),
        ]), [{"texts": ["English"]}, {"texts": [None]}, {"texts": []}])

    def test_invalid_batches_preserve_input(self):
        for value in (None, {}, (), "payloads", 3,
                      [payload(), None], [payload(), payload(locales=[""])]):
            with self.subTest(value=value):
                before = copy.deepcopy(value)
                with self.assertRaises(ValueError):
                    service.batch(value)
                self.assertEqual(value, before)


class CLI(unittest.TestCase):
    def run_cli(self, *args, stdin=""):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, "-B", str(repo / "cli.py"), *args],
            cwd=repo, input=stdin, capture_output=True, text=True, timeout=5,
        )

    def test_json_translation_and_service_parity(self):
        value = payload(catalog={"fr": {"a": "été", "b": ""},
                                 "en": {"c": "default"}},
                        locales=["fr-CA"], keys=["a", "b", "c", "x", "a"])
        expected = {"texts": ["été", "", "default", None, "été"]}
        self.assertEqual(app.process(value), expected)
        self.assertEqual(service.handle(value), expected)
        result = self.run_cli(stdin=json.dumps(value))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(result.stderr, "")

    def test_invalid_json_and_payloads(self):
        for stdin in ("{", "null", "{}", json.dumps(payload(default=None))):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin=stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_exact_behavior(self):
        for args in (("--unknown",), ("--version", "extra")):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

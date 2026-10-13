import copy
import json
import pathlib
import subprocess
import sys
import unittest

from app import process
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


class TranslationTests(unittest.TestCase):
    def test_each_key_uses_requested_chains_before_default(self):
        value = payload(
            catalog={
                "zh-Hant-TW": {"exact": "exact", "empty": ""},
                "zh-Hant": {"script": "script", "empty": "parent"},
                "zh": {"language": "language", "priority": "parent"},
                "fr": {"priority": "later", "later": "later"},
                "en": {"default": "default", "priority": "default"},
            },
            locales=["zh-Hant-TW", "fr"],
            keys=["exact", "script", "language", "priority", "later",
                  "default", "missing", "empty", "exact"],
        )
        before = copy.deepcopy(value)
        self.assertEqual(process(value), {"texts": [
            "exact", "script", "language", "parent", "later", "default",
            None, "", "exact",
        ]})
        self.assertEqual(value, before)

    def test_default_is_exact_and_requested_can_truncate_same_locale(self):
        value = payload(catalog={"en": {"a": "parent"}},
                        locales=[], default="en-US")
        self.assertEqual(process(value), {"texts": [None]})
        value["locales"] = ["en-US"]
        self.assertEqual(process(value), {"texts": ["parent"]})

    def test_empty_containers_and_empty_default_translation(self):
        self.assertEqual(process(payload(catalog={}, locales=[], keys=[])),
                         {"texts": []})
        self.assertEqual(process(payload(catalog={}, locales=[])),
                         {"texts": [None]})
        self.assertEqual(process(payload(catalog={"en": {"a": ""}}, locales=[])),
                         {"texts": [""]})

    def test_matching_is_case_sensitive(self):
        value = payload(catalog={"EN": {"a": "upper locale"},
                                 "en": {"A": "upper key"}},
                        locales=["en"], keys=["a", "A"], default="en")
        self.assertEqual(process(value), {"texts": [None, "upper key"]})

    def test_names_have_no_language_grammar_restrictions(self):
        value = payload(
            catalog={" odd name ": {" ": "space"},
                     "-": {"!": "dash"},
                     "a-": {"!": "trailing dash"},
                     "日本語": {"雪": "❄"}},
            locales=[" odd name -child", "--child", "a--child", "日本語"],
            keys=[" ", "!", "雪"], default="unused",
            extra={"ignored": None},
        )
        self.assertEqual(process(value), {"texts": ["space", "dash", "❄"]})
        value["locales"] = ["a--child"]
        self.assertEqual(process(value), {"texts": [None, "trailing dash", None]})

    def test_malformed_values_raise_value_error_without_mutation(self):
        invalid = [None, [], "payload", 42, True]
        for field in ("catalog", "locales", "keys", "default"):
            missing = payload()
            del missing[field]
            invalid.append(missing)
        for value in (None, [], "catalog", 1, True):
            invalid.append(payload(catalog=value))
        for field in ("locales", "keys"):
            for value in (None, {}, "en", ("en",), 1, True):
                invalid.append(payload(**{field: value}))
            for value in ("", None, 1, True, [], {}):
                invalid.append(payload(**{field: ["valid", value]}))
        for value in ("", None, 1, True, [], {}):
            invalid.append(payload(default=value))
        for locale in ("", None, 1, False):
            invalid.append(payload(catalog={locale: {}}))
        for translations in (None, [], "text", 1, True):
            invalid.append(payload(catalog={"unused": translations}))
        for key in ("", None, 1, False):
            invalid.append(payload(catalog={"unused": {key: "text"}}))
        for translation in (None, [], {}, 1, True):
            invalid.append(payload(catalog={"unused": {"unused": translation}}))
        # Validate even when there are no output keys or all lookups would succeed.
        invalid.extend([
            payload(keys=[], catalog={"unused": {"a": None}}),
            payload(keys=[], locales=[None]),
            payload(keys=[], default=None),
            payload(catalog={"en": {"a": "found"}, "unused": {"b": None}}),
        ])
        for value in invalid:
            with self.subTest(value=value):
                before = copy.deepcopy(value)
                with self.assertRaises(ValueError):
                    process(value)
                self.assertEqual(value, before)


class ServiceTests(unittest.TestCase):
    def test_handle_and_batch_preserve_order_and_inputs(self):
        first = payload()
        second = payload(catalog={}, keys=["a", "a"])
        values = [first, second, first]
        before = copy.deepcopy(values)
        self.assertEqual(service.handle(first), {"texts": ["English"]})
        self.assertEqual(service.batch(values), [
            {"texts": ["English"]}, {"texts": [None, None]},
            {"texts": ["English"]},
        ])
        self.assertEqual(service.batch([]), [])
        self.assertEqual(values, before)

    def test_invalid_batches_and_handle_raise_value_error(self):
        for value in (None, {}, "batch", (), 1, [payload(), None],
                      [payload(), payload(keys=[""])]):
            with self.subTest(value=value):
                before = copy.deepcopy(value)
                with self.assertRaises(ValueError):
                    service.batch(value)
                self.assertEqual(value, before)
        with self.assertRaises(ValueError):
            service.handle({})


class CliTests(unittest.TestCase):
    def run_cli(self, stdin="", arguments=()):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, "-B", str(repo / "cli.py"), *arguments],
            cwd=repo, input=stdin, capture_output=True, text=True, timeout=5,
        )

    def test_json_translation(self):
        value = payload(catalog={"fr": {"a": "été", "b": ""}},
                        locales=["fr-CA"], keys=["b", "a", "missing", "a"])
        result = self.run_cli(json.dumps(value))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout),
                         {"texts": ["", "été", None, "été"]})
        self.assertIn("été", result.stdout)

    def test_invalid_payload_and_json(self):
        for stdin in ("{}", "null", "[]", "{broken", json.dumps(payload(keys=[0]))):
            with self.subTest(stdin=stdin):
                result = self.run_cli(stdin)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments(self):
        for arguments in (("--unknown",), ("--version", "extra"), ("--help",)):
            with self.subTest(arguments=arguments):
                result = self.run_cli(arguments=arguments)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

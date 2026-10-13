import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


def payload(**overrides):
    value = {"catalog": {}, "locales": [], "keys": [], "default": "en"}
    value.update(overrides)
    return value


class TranslationTests(unittest.TestCase):
    def test_per_key_order_and_duplicates(self):
        value = payload(
            catalog={
                "zh-Hant-TW": {"exact": "TW"},
                "zh-Hant": {"parent": "Hant"},
                "zh": {"root": "zh", "priority": "first parent"},
                "fr": {"priority": "second exact", "later": "fr"},
                "en": {"default": "en"},
            },
            locales=["zh-Hant-TW", "fr"],
            keys=["parent", "exact", "root", "priority", "later", "default", "missing", "exact"],
        )
        self.assertEqual(app.process(value), {"texts": [
            "Hant", "TW", "zh", "first parent", "fr", "en", None, "TW"
        ]})

    def test_empty_translation_is_found(self):
        value = payload(catalog={"fr": {"a": ""}, "en": {"a": "fallback"}},
                        locales=["fr-CA"], keys=["a"])
        self.assertEqual(app.process(value), {"texts": [""]})

    def test_default_is_exact_only(self):
        value = payload(catalog={"en": {"a": "parent"}, "en-US": {"b": "exact"}},
                        default="en-US", keys=["a", "b"])
        self.assertEqual(app.process(value), {"texts": [None, "exact"]})
        value["locales"] = ["en-US"]
        self.assertEqual(app.process(value), {"texts": ["parent", "exact"]})

    def test_case_sensitive(self):
        value = payload(catalog={"FR": {"a": "upper locale"}, "fr": {"A": "upper key"}},
                        locales=["fr"], keys=["a", "A"], default="EN")
        self.assertEqual(app.process(value), {"texts": [None, "upper key"]})

    def test_no_locale_grammar_restrictions(self):
        value = payload(catalog={"odd--": {"a": "exact"}, "odd-": {"b": "parent"},
                                 "odd": {"c": "root"}, "-": {"d": "hyphen"},
                                 " ": {"e": "space"}, "_!": {"f": "punctuation"}},
                        locales=["odd--", "-", " ", "_!"],
                        keys=["a", "b", "c", "d", "e", "f"])
        self.assertEqual(app.process(value), {"texts": [
            "exact", "parent", "root", "hyphen", "space", "punctuation"
        ]})

    def test_empty_containers_and_extra_fields(self):
        self.assertEqual(app.process(payload(extra=None)), {"texts": []})
        self.assertEqual(app.process(payload(keys=["a", "a"])), {"texts": [None, None]})
        self.assertEqual(app.process(payload(catalog={"en": {"a": "default"}}, keys=["a"])),
                         {"texts": ["default"]})

    def test_invalid_payloads_raise_valueerror_without_mutation(self):
        invalid = [None, [], "", 1, {}, {"catalog": {}},
                   payload(catalog=[]), payload(locales=()), payload(keys={}),
                   payload(default=""), payload(default=None)]
        for field in ("locales", "keys"):
            for bad in ("", None, 0, False, {}, []):
                invalid.append(payload(**{field: [bad]}))
        for bad in ("", None, 1):
            invalid.append(payload(catalog={bad: {}}))
            invalid.append(payload(catalog={"unused": {bad: "text"}}))
        for bad in (None, [], "text", 1):
            invalid.append(payload(catalog={"unused": bad}))
        for bad in (None, [], {}, 1, False):
            invalid.append(payload(catalog={"unused": {"a": bad}}))
        for value in invalid:
            before = copy.deepcopy(value)
            with self.subTest(value=value):
                for entrypoint in (app.process, service.handle):
                    with self.assertRaises(ValueError):
                        entrypoint(value)
                self.assertEqual(value, before)

    def test_handle_and_batch_preserve_order_and_input(self):
        first = payload(catalog={"fr": {"a": ""}}, locales=["fr-CA"], keys=["a", "x", "a"])
        values = [first, payload(keys=["missing"]), first]
        before = copy.deepcopy(values)
        self.assertEqual(service.handle(first), {"texts": ["", None, ""]})
        self.assertEqual(service.batch(values), [
            {"texts": ["", None, ""]}, {"texts": [None]}, {"texts": ["", None, ""]}
        ])
        self.assertEqual(values, before)
        self.assertEqual(service.batch([]), [])

    def test_batch_rejects_invalid_container_and_members(self):
        for value in (None, {}, (), "", [payload(), payload(catalog={"en": {"a": None}})]):
            before = copy.deepcopy(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                service.batch(value)
            self.assertEqual(value, before)


class CliTests(unittest.TestCase):
    def run_cli(self, value, *arguments):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-B", str(repo / "cli.py"), *arguments],
                              input=json.dumps(value), cwd=repo, capture_output=True,
                              text=True, timeout=5)

    def test_json_cli(self):
        result = self.run_cli(payload(catalog={"fr": {"a": "été"}},
                                      locales=["fr-CA"], keys=["a", "x", "a"]))
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(json.loads(result.stdout), {"texts": ["été", None, "été"]})

    def test_invalid_cli_payload(self):
        result = self.run_cli(payload(catalog={"fr": {"a": None}}))
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_unchanged(self):
        for arguments in (("--unknown",), ("--version", "extra")):
            with self.subTest(arguments=arguments):
                result = self.run_cli(payload(), *arguments)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, "", "ERROR: unsupported arguments\n"))

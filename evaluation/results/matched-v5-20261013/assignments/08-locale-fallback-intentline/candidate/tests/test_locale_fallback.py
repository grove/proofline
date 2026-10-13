import copy
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


def payload(**changes):
    value = {
        "catalog": {"en": {"a": "English"}},
        "locales": ["en"],
        "keys": ["a"],
        "default": "en",
    }
    value.update(changes)
    return value


class LocaleFallback(unittest.TestCase):
    def test_each_key_uses_its_own_fallback_chain(self):
        value = payload(
            catalog={
                "zh-Hant-TW": {"exact": "TW", "empty": ""},
                "zh-Hant": {"script": "Hant", "empty": "wrong"},
                "zh": {"language": "zh", "priority": "parent"},
                "fr-CA": {"priority": "second exact", "other": "CA"},
                "en": {"default": "EN", "empty": "wrong"},
            },
            locales=["zh-Hant-TW", "fr-CA"],
            keys=["script", "exact", "language", "priority", "other",
                  "default", "missing", "exact", "empty"],
        )
        self.assertEqual(
            app.process(value),
            {"texts": ["Hant", "TW", "zh", "parent", "CA", "EN",
                       None, "TW", ""]},
        )

    def test_missing_exact_locale_still_tries_all_parents(self):
        self.assertEqual(
            app.process(payload(catalog={"aa": {"a": "parent"}},
                                locales=["aa-bb-cc"])),
            {"texts": ["parent"]},
        )

    def test_default_is_exact_and_is_after_all_requested_chains(self):
        catalog = {"en": {"a": "parent"}, "fr": {"b": "requested"},
                   "en-US": {"b": "default", "c": ""}}
        self.assertEqual(
            app.process(payload(catalog=catalog, locales=["fr-CA"],
                                keys=["a", "b", "c"], default="en-US")),
            {"texts": [None, "requested", ""]},
        )
        self.assertEqual(
            app.process(payload(catalog=catalog, locales=[], keys=["a"],
                                default="en-GB")),
            {"texts": [None]},
        )

    def test_default_can_be_truncated_when_it_is_also_requested(self):
        self.assertEqual(
            app.process(payload(locales=["en-US"], default="en-US")),
            {"texts": ["English"]},
        )

    def test_locale_and_key_matching_are_case_sensitive(self):
        self.assertEqual(
            app.process(payload(catalog={"EN": {"a": "upper locale"},
                                         "en": {"A": "upper key"}},
                                locales=["en"], keys=["a", "A"],
                                default="En")),
            {"texts": [None, "upper key"]},
        )

    def test_empty_containers(self):
        cases = [
            (payload(catalog={}, locales=[], keys=[]), {"texts": []}),
            (payload(catalog={}, locales=[], keys=["a", "a"]),
             {"texts": [None, None]}),
            (payload(locales=[]), {"texts": ["English"]}),
            (payload(catalog={"en": {}}, keys=["a"]), {"texts": [None]}),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(app.process(value), expected)

    def test_unusual_names_extra_keys_and_unicode_are_accepted(self):
        self.assertEqual(
            app.process(payload(
                catalog={" odd_name ": {"\t": "你好"}},
                locales=[" odd_name -extension"], keys=["\t"],
                default="☃", extra={"arbitrary": [None, 1]},
            )),
            {"texts": ["你好"]},
        )

    def test_hyphen_truncation_does_not_require_valid_bcp47(self):
        value = payload(
            catalog={"x--": {"exact": "exact"},
                     "x-": {"mid": "mid"}, "x": {"root": "root"},
                     "-x": {"leading": "leading"},
                     "-": {"dash": "dash"}},
            locales=["x--", "-x", "-"],
            keys=["exact", "mid", "root", "leading", "dash"],
        )
        self.assertEqual(app.process(value),
                         {"texts": ["exact", "mid", "root", "leading", "dash"]})


class Validation(unittest.TestCase):
    def test_invalid_payloads_raise_valueerror_without_mutation(self):
        invalid = [None, [], "payload", 1, True, {}]
        for field in ("catalog", "locales", "keys", "default"):
            value = payload()
            del value[field]
            invalid.append(value)
        for value in (None, [], (), "en", 1, False):
            invalid.append(payload(catalog=value))
        for field in ("locales", "keys"):
            for value in (None, {}, (), "en", 1, False,
                          [""], [None], [1], [False], [[]], ["en", ""]):
                invalid.append(payload(**{field: value}))
        for value in (None, "", [], {}, 1, True):
            invalid.append(payload(default=value))
        for value in (None, [], (), "text", 1, False):
            invalid.append(payload(catalog={"en": value}))
        for name in ("", None, 1, False):
            invalid.append(payload(catalog={name: {"a": "text"}}))
            invalid.append(payload(catalog={"en": {name: "text"}}))
        for text in (None, 1, False, [], {}, ("text",)):
            invalid.append(payload(catalog={"en": {"a": text}}))
        # Bad data must be rejected even if no key or locale would reach it.
        invalid.append(payload(catalog={"unused": {"a": None}},
                               locales=[], keys=[]))
        invalid.append(payload(catalog={"en": {"a": "valid"},
                                        "unused": {"b": 1}}))
        for function in (app.process, service.handle):
            for value in invalid:
                with self.subTest(function=function.__name__, value=value):
                    before = copy.deepcopy(value)
                    with self.assertRaises(ValueError):
                        function(value)
                    self.assertEqual(value, before)

    def test_success_does_not_mutate_and_results_are_fresh(self):
        value = payload(keys=["a", "a", "missing"], extra=[1, 2])
        before = copy.deepcopy(value)
        for function in (app.process, service.handle):
            self.assertEqual(function(value),
                             {"texts": ["English", "English", None]})
            self.assertEqual(value, before)
            result = function(value)
            result["texts"].clear()
            self.assertEqual(value, before)
            self.assertEqual(function(value),
                             {"texts": ["English", "English", None]})


class Batch(unittest.TestCase):
    def test_order_empty_duplicates_and_no_mutation(self):
        first = payload()
        second = payload(catalog={"fr": {"a": ""}}, locales=["fr"])
        values = [second, first, second]
        before = copy.deepcopy(values)
        result = service.batch(values)
        self.assertEqual(result, [{"texts": [""]}, {"texts": ["English"]},
                                  {"texts": [""]}])
        self.assertEqual(values, before)
        result[0]["texts"].append("changed")
        self.assertEqual(result[2], {"texts": [""]})
        self.assertEqual(values, before)
        self.assertEqual(service.batch([]), [])

    def test_invalid_container_or_member_does_not_mutate(self):
        for values in (None, {}, (), "payloads", 1, True,
                       [None, payload()], [payload(), None],
                       [payload(), payload(catalog={"en": {"a": 1}})]):
            with self.subTest(values=values):
                before = copy.deepcopy(values)
                with self.assertRaises(ValueError):
                    service.batch(values)
                self.assertEqual(values, before)


class Cli(unittest.TestCase):
    def run_cli(self, value=None, args=(), raw=None):
        repo = pathlib.Path(__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, "-B", str(repo / "cli.py"), *args], cwd=repo,
            input=raw if raw is not None else json.dumps(value),
            capture_output=True, text=True, timeout=5,
        )

    def test_json_translation_matches_public_apis(self):
        value = payload(catalog={"fr": {"a": "été", "b": ""}},
                        locales=["fr-CA"], keys=["b", "a", "x", "a"])
        expected = {"texts": ["", "été", None, "été"]}
        self.assertEqual(app.process(value), expected)
        self.assertEqual(service.handle(value), expected)
        result = self.run_cli(value)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), expected)

    def test_invalid_input(self):
        for value in (None, {}, payload(catalog={"en": {"a": None}})):
            with self.subTest(value=value):
                result = self.run_cli(value)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("ERROR: "))
        result = self.run_cli(raw="{")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("ERROR: "))

    def test_unsupported_arguments_are_unchanged(self):
        for args in (("--bogus",), ("--version", "extra"), ("value",)):
            with self.subTest(args=args):
                result = self.run_cli(args=args, raw="invalid JSON")
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (2, "", "ERROR: unsupported arguments\n"),
                )


if __name__ == "__main__":
    unittest.main()

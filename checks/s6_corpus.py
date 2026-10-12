"""Private pilot corpus. Never expose this module or its controls to workers."""
from __future__ import annotations

import textwrap

APP = '''import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import process

def main():
    if sys.argv[1:] == ["--version"]:
        print("pilot-tool 1.0")
        return 0
    try:
        if len(sys.argv) != 2:
            raise ValueError("one JSON argument required")
        value = process(json.loads(sys.argv[1]))
        print(json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
'''


def task(name, requirement, seed, good, probes, *, alternative=None, tags=()):
    def code(value):
        lines = value.splitlines()
        if len(lines) > 1 and len(lines[1]) - len(lines[1].lstrip()) >= 9:
            value = '         ' + value
        return textwrap.dedent(value).strip() + '\n'
    return {"id": name, "requirement": requirement,
            "seed": code(seed),
            "good": code(good),
            "alternative": code(alternative) if alternative else None,
            "probes": [{"input": value, "expected": expected} for value, expected in probes],
            "tags": list(tags)}


TASKS = [
    task("unicode-usernames", "Reject empty or Unicode whitespace-only username strings with ValueError; return every valid username unchanged, including surrounding whitespace and zero-width spaces.",
         'def process(data):\n    if not data: raise ValueError("blank")\n    return data',
         'WHITE_SPACE = "\\u0009\\u000a\\u000b\\u000c\\u000d\\u0020\\u0085\\u00a0\\u1680\\u2000\\u2001\\u2002\\u2003\\u2004\\u2005\\u2006\\u2007\\u2008\\u2009\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000"\ndef process(data):\n    if not isinstance(data, str) or not data.strip(WHITE_SPACE): raise ValueError("blank")\n    return data',
         [("alice", "alice"), ("  Åse  ", "  Åse  "), ("\u200b", "\u200b"), ("\u0085\u2003", {"error": True}), ("", {"error": True}), ("\u001c\u001d\u001e\u001f", "\u001c\u001d\u001e\u001f")],
         alternative='def process(data):\n    if not isinstance(data, str) or not data or all(c.isspace() and c not in "\\u001c\\u001d\\u001e\\u001f" for c in data): raise ValueError("blank")\n    return data', tags=("simple-bug", "alternative")),
    task("stable-pagination", "Input has rows (objects with id and score), offset and limit. Sort score descending then id ascending; return that slice. Offset and limit must be nonnegative integers (booleans invalid). Never drop tied rows; preserve their other fields.",
         'def process(data):\n    return sorted(data["rows"], key=lambda r: -r["score"])[data["offset"]:][:data["limit"]]',
         '''from functools import cmp_to_key
         def process(data):
             offset, limit = data["offset"], data["limit"]
             if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in (offset, limit)): raise ValueError("bad page")
             for row in data["rows"]: row["score"], row["id"]
             def compare(a, b):
                 if a["score"] != b["score"]: return -1 if a["score"] > b["score"] else 1
                 if a["id"] == b["id"]: return 0
                 return -1 if a["id"] < b["id"] else 1
             return sorted(data["rows"], key=cmp_to_key(compare))[offset:offset+limit]''',
         [({"rows": [{"id": "b", "score": 2}, {"id": "a", "score": 2}, {"id": "c", "score": 1}], "offset": 0, "limit": 2}, [{"id": "a", "score": 2}, {"id": "b", "score": 2}]), ({"rows": [], "offset": 0, "limit": 0}, []), ({"rows": [], "offset": -1, "limit": 2}, {"error": True}), ({"rows": [], "offset": True, "limit": 2}, {"error": True}),
          ({"rows": [{"id": "b", "score": "z", "extra": 1}, {"id": "a", "score": "a"}, {"id": "a", "score": "z"}], "offset": 0, "limit": 3}, [{"id": "a", "score": "z"}, {"id": "b", "score": "z", "extra": 1}, {"id": "a", "score": "a"}]),
          ({"rows": [{"id": 1, "score": 2}, {"id": "a", "score": 1}], "offset": 0, "limit": 2}, [{"id": 1, "score": 2}, {"id": "a", "score": 1}]),
          ({"rows": [{"id": "only"}], "offset": 0, "limit": 1}, {"error": True})],
         alternative='''def process(data):
             offset, limit = data["offset"], data["limit"]
             if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in (offset, limit)): raise ValueError("bad page")
             ordered = []
             for row in data["rows"]:
                 row["score"], row["id"]
                 position = 0
                 for other in ordered:
                     if (row["score"] != other["score"] and row["score"] > other["score"]) or (row["score"] == other["score"] and row["id"] != other["id"] and row["id"] < other["id"]): break
                     position += 1
                 ordered.insert(position, row)
             return ordered[offset:offset+limit]''', tags=("multiple-criteria", "alternative")),
    task("quoted-csv", "Parse a CSV string with a header into dictionaries of strings using standard CSV quoting, embedded commas/newlines, CRLF and empty fields. Empty input returns []; reject duplicate header names and ragged data rows with ValueError.",
         'def process(data):\n    lines=data.splitlines()\n    if not lines: return []\n    return [dict(zip(lines[0].split(","), line.split(","))) for line in lines[1:]]',
         '''import csv, io
         def process(data):
             previous = csv.field_size_limit()
             try:
                 csv.field_size_limit(max(previous, len(data)))
                 rows = list(csv.reader(io.StringIO(data, newline="")))
             finally: csv.field_size_limit(previous)
             if not rows: return []
             header = rows[0]
             if len(set(header)) != len(header) or any(len(row) != len(header) for row in rows[1:]): raise ValueError("bad CSV")
             return [dict(zip(header, row)) for row in rows[1:]]''',
         [("name,note\r\nÅse,\"a,b\"\r\nBob,\"line1\nline2\"\r\n", [{"name": "Åse", "note": "a,b"}, {"name": "Bob", "note": "line1\nline2"}]), ("a,b\n,\n", [{"a": "", "b": ""}]), ("", []), ("a,a\n1,2\n", {"error": True}), ("a,b\n1\n", {"error": True}), ("name\n" + "x" * 131073 + "\n", [{"name": "x" * 131073}])], tags=("green-tests-regression",)),
    task("decimal-invoices", "Input is a list of lines with decimal-string price and nonnegative integer quantity. Return the total as a two-decimal string, rounding each line HALF_UP before summing. Reject negative/nonfinite prices and invalid quantities (including bool). Empty invoices return 0.00.",
         'def process(data):\n    return format(sum(float(r["price"])*r["quantity"] for r in data), ".2f")',
         '''from decimal import Decimal, ROUND_HALF_UP
         def process(data):
             total = Decimal("0")
             for row in data:
                 price, quantity = Decimal(row["price"]), row["quantity"]
                 if not price.is_finite() or price < 0 or type(quantity) is not int or quantity < 0: raise ValueError("invalid line")
                 total += (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
             return format(total, ".2f")''',
         [([{"price": "0.005", "quantity": 1}, {"price": "0.005", "quantity": 1}], "0.02"), ([{"price": "2.675", "quantity": 1}], "2.68"), ([], "0.00"), ([{"price": "NaN", "quantity": 1}], {"error": True}), ([{"price": "1", "quantity": True}], {"error": True})], tags=("boundary",)),
    task("merge-settings", "Deep merge input base and override JSON objects without mutating inputs: nested objects merge, lists/scalars replace, null deletes the key (also when absent). Objects introduced by override still apply null deletion recursively. Return {merged, base, override}, retaining the original base and override.",
         'def process(data):\n    return {"merged":dict(data["base"], **data["override"]), **data}',
         '''import copy
         def merge(base, override):
             result = copy.deepcopy(base)
             for key, value in override.items():
                 if value is None: result.pop(key, None)
                 elif isinstance(value, dict): result[key] = merge(result.get(key, {}) if isinstance(result.get(key), dict) else {}, value)
                 else: result[key] = copy.deepcopy(value)
             return result
         def process(data):
             return {"merged": merge(data["base"], data["override"]), "base": data["base"], "override": data["override"]}''',
         [({"base": {"a": {"x": 1, "y": 2}, "l": [1]}, "override": {"a": {"x": None, "z": 3}, "l": []}}, {"merged": {"a": {"y": 2, "z": 3}, "l": []}, "base": {"a": {"x": 1, "y": 2}, "l": [1]}, "override": {"a": {"x": None, "z": 3}, "l": []}}), ({"base": {}, "override": {"a": {"x": None}}}, {"merged": {"a": {}}, "base": {}, "override": {"a": {"x": None}}})], tags=("omitted-obligation",)),
    task("safe-archive-paths", "For a list of POSIX archive member names, return each unchanged if safe. Reject the whole list for empty, absolute, backslash-containing, drive-prefixed (letter colon), or any '..' segment. Ordinary '.' segments and Unicode are allowed. No filesystem access.",
         'def process(data):\n    if any(n.startswith("/") for n in data): raise ValueError("unsafe")\n    return data',
         '''import re
         def process(data):
             for name in data:
                 if not name or name.startswith("/") or "\\\\" in name or re.match(r"^[A-Za-z]:", name) or ".." in name.split("/"): raise ValueError("unsafe")
             return data''',
         [(["docs/Åse.txt", "./a", "a..b"], ["docs/Åse.txt", "./a", "a..b"]), (["a/../b"], {"error": True}), (["C:escape"], {"error": True}), (["a\\b"], {"error": True}), ([""], {"error": True}), ([], [])], tags=("security",)),
    task("interval-union", "Merge a list of integer [start,end] intervals including touching intervals, sorted by start. Reject reversed intervals; zero-length intervals are valid. Return [] for empty input and preserve all covered endpoints.",
         'def process(data):\n    return sorted(data)',
         '''def process(data):
             if any(a > b for a, b in data): raise ValueError("reversed")
             result = []
             for a, b in sorted(data):
                 if result and a <= result[-1][1]: result[-1][1] = max(b, result[-1][1])
                 else: result.append([a, b])
             return result''',
         [([[5, 7], [1, 3], [3, 5], [2, 2], [10, 10]], [[1, 7], [10, 10]]), ([[4, 2]], {"error": True}), ([], []), ([[1, 8], [2, 3]], [[1, 8]])],
         alternative='''def process(data):
             if any(a > b for a, b in data): raise ValueError("reversed")
             result = []
             for a, b in sorted(data):
                 while result and a <= result[-1][1]:
                     x, y = result.pop(); a, b = min(x, a), max(y, b)
                 result.append([a, b])
             return result''', tags=("alternative",)),
    task("dependency-order", "Input maps job names to dependency lists. Return a topological order, repeatedly selecting the lexicographically smallest currently ready job. Duplicate dependencies count once. Reject unknown dependencies or cycles. Empty graph returns [].",
         'def process(data):\n    return sorted(data)',
         '''def process(data):
             deps = {name: set(values) for name, values in data.items()}
             if any(values - deps.keys() for values in deps.values()): raise ValueError("unknown dependency")
             result = []
             while deps:
                 ready = sorted(name for name, values in deps.items() if not values)
                 if not ready: raise ValueError("cycle")
                 name = ready[0]; result.append(name); del deps[name]
                 for values in deps.values(): values.discard(name)
             return result''',
         [({"a": ["c"], "b": [], "c": ["b", "b"]}, ["b", "c", "a"]), ({"a": ["a"]}, {"error": True}), ({"a": ["x"]}, {"error": True}), ({"a": [], "b": [], "c": ["a"]}, ["a", "b", "c"]), ({}, [])], tags=("larger-autonomy",)),
    task("retry-schedule", "Input base and cap are nonnegative numbers, attempts is a nonnegative integer (not bool). Return min(cap, base*2**i) for each i from 0 to attempts-1. Reject invalid or negative inputs; attempts=0 returns []. Avoid computing huge powers once capped.",
         'def process(data):\n    return [data["base"]*2**i for i in range(data["attempts"])]',
         '''def process(data):
             base, cap, n = data["base"], data["cap"], data["attempts"]
             if type(n) is not int or n < 0 or type(base) not in (int, float) or type(cap) not in (int, float) or min(base, cap) < 0: raise ValueError("invalid schedule")
             result = []; value = min(base, cap)
             for _ in range(n): result.append(value); value = min(cap, value * 2)
             return result''',
         [({"base": 3, "cap": 10, "attempts": 5}, [3, 6, 10, 10, 10]), ({"base": 5, "cap": 0, "attempts": 3}, [0, 0, 0]), ({"base": 1, "cap": 3, "attempts": 0}, []), ({"base": -1, "cap": 4, "attempts": 2}, {"error": True}), ({"base": 1, "cap": 4, "attempts": True}, {"error": True})], tags=("long-tail",)),
    task("utc-timestamps", "Convert ISO-8601 strings with explicit UTC offset or Z to UTC formatted YYYY-MM-DDTHH:MM:SSZ; fractions are truncated. Reject naive timestamps and malformed inputs. Correctly handle date rollover and non-hour offsets.",
         'def process(data):\n    return data.replace("+00:00", "Z")',
         '''from datetime import datetime, timedelta, timezone
         import re
         def process(data):
             if not isinstance(data, str) or "T" not in data: raise ValueError("ISO date/time required")
             ordinal = re.fullmatch(r"([0-9]{4})-?([0-9]{3})(T.+)", data)
             if ordinal:
                 year, day = int(ordinal[1]), int(ordinal[2])
                 date = datetime(year, 1, 1) + timedelta(days=day - 1)
                 if day < 1 or date.year != year: raise ValueError("invalid ordinal date")
                 data = date.date().isoformat() + ordinal[3]
             date, clock = data.split("T")
             if not re.search(r"(?:Z|[+-](?:[01][0-9]|2[0-3])(?::?[0-5][0-9])?)$", clock): raise ValueError("invalid offset")
             midnight = re.fullmatch(r"24(?::?00)?(?::?00)?(?:[.,]0+)?(Z|[+-][0-9]{2}(?::?[0-9]{2})?)", clock)
             if midnight: clock = "00:00:00" + midnight[1]
             value = datetime.fromisoformat(date + "T" + clock)
             if midnight: value += timedelta(days=1)
             if value.tzinfo is None: raise ValueError("offset required")
             return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")''',
         [("2026-01-01T00:15:01+01:00", "2025-12-31T23:15:01Z"), ("2026-01-01T12:00:02.999+05:30", "2026-01-01T06:30:02Z"), ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"), ("2026-01-01T00:00:00", {"error": True}), ("bad", {"error": True}), ("2024-061T00:15:30+05:45", "2024-02-29T18:30:30Z"), ("2024061T001530+0545", "2024-02-29T18:30:30Z"), ("2024-02-29T24:00:00Z", "2024-03-01T00:00:00Z"), ("2024-01-01x00:00:00Z", {"error": True}), ("2024-01-01T00:00:00+01:02:03", {"error": True}), ("0001-001T00:00:00Z", "0001-01-01T00:00:00Z")]),
    task("query-multimap", "Parse a URL query string to an ordered list of [key,value] pairs, preserving repeated keys, blank values, Unicode and field order. Percent-decode UTF-8 and interpret plus as space. Empty string returns []; fields without '=' have empty values.",
         'def process(data):\n    return [part.split("=", 1) for part in data.split("&") if part]',
         '''from urllib.parse import parse_qsl
         def process(data):
             return [list(pair) for pair in parse_qsl(data, keep_blank_values=True)]''',
         [("a=1&a=&name=%C3%85se+X&flag", [["a", "1"], ["a", ""], ["name", "Åse X"], ["flag", ""]]), ("", []), ("x=a%3Db%26c&%2B=+", [["x", "a=b&c"], ["+", " "]])]),
    task("version-order", "Sort strings of exactly three nonnegative decimal integer components (major.minor.patch) numerically, stably preserving equal versions. Leading zeros allowed. Reject missing components, signs, non-ASCII digits and prerelease suffixes.",
         'def process(data):\n    return sorted(data)',
         '''import re
         def process(data):
             if any(not re.fullmatch(r"[0-9]+\\.[0-9]+\\.[0-9]+", v) for v in data): raise ValueError("invalid version")
             def key(version):
                 parts = [part.lstrip("0") or "0" for part in version.split(".")]
                 return tuple((len(part), part) for part in parts)
             return sorted(data, key=key)''',
         [(["1.10.0", "1.2.0", "01.2.0", "0.9.9"], ["0.9.9", "1.2.0", "01.2.0", "1.10.0"]), (["1.2"], {"error": True}), (["1.2.3-beta"], {"error": True}), (["-1.2.3"], {"error": True}), (["١.2.3"], {"error": True}), ([], []), (["1" * 5000 + ".0.0", "9.0.0"], ["9.0.0", "1" * 5000 + ".0.0"])]),
    task("redact-secrets", "Recursively redact dictionary values whose key case-insensitively equals password, token or secret, replacing them with '[REDACTED]'. Walk nested dictionaries and lists, preserve all other values including substrings such as token_count. Return {redacted, original} with original input unchanged.",
         'def process(data):\n    return {"redacted": data, "original": data}',
         '''def redact(value):
             if isinstance(value, dict): return {k: "[REDACTED]" if k.lower() in {"password", "token", "secret"} else redact(v) for k, v in value.items()}
             if isinstance(value, list): return [redact(v) for v in value]
             return value
         def process(data):
             return {"redacted": redact(data), "original": data}''',
         [({"Token": "x", "rows": [{"PASSWORD": "y", "token_count": 2}], "n": None}, {"redacted": {"Token": "[REDACTED]", "rows": [{"PASSWORD": "[REDACTED]", "token_count": 2}], "n": None}, "original": {"Token": "x", "rows": [{"PASSWORD": "y", "token_count": 2}], "n": None}}), ([{"secret": [1]}], {"redacted": [{"secret": "[REDACTED]"}], "original": [{"secret": [1]}]})], tags=("held-out", "security")),
    task("json-pointer", "Resolve input pointer against document using RFC6901 string syntax: '' returns whole document; slash-separated segments decode ~1 to '/' then ~0 to '~'. Object keys may be empty. Array indices must be canonical nonnegative decimals, no leading zeros except '0'; '-' is invalid. Reject missing paths, malformed escapes or invalid pointer syntax with ValueError.",
         'def process(data):\n    return data["document"][data["pointer"].lstrip("/")]',
         '''import re
         def process(data):
             value, pointer = data["document"], data["pointer"]
             if pointer == "": return value
             if not pointer.startswith("/"): raise ValueError("invalid pointer")
             for part in pointer[1:].split("/"):
                 if re.search(r"~(?:[^01]|$)", part): raise ValueError("invalid escape")
                 part = part.replace("~1", "/").replace("~0", "~")
                 try:
                     if isinstance(value, list):
                         if not re.fullmatch(r"0|[1-9][0-9]*", part): raise ValueError("bad index")
                         value = value[int(part)]
                     elif isinstance(value, dict): value = value[part]
                     else: raise ValueError("scalar")
                 except (IndexError, KeyError) as error: raise ValueError("missing path") from error
             return value''',
         [({"document": {"a/b": {"~": [10, 20]}}, "pointer": "/a~1b/~0/1"}, 20), ({"document": {"": 7}, "pointer": "/"}, 7), ({"document": [3], "pointer": ""}, [3]), ({"document": [3], "pointer": "/00"}, {"error": True}), ({"document": {}, "pointer": "/~2"}, {"error": True}), ({"document": [3], "pointer": "/9"}, {"error": True})], tags=("held-out", "long-tail")),
    task("ttl-cache", "Simulate a cache from operations: set(key,value,now,ttl), get(key,now), delete(key,now). Return one result per operation: null for set/delete; value or null for get. Expire at now >= set_time+ttl; ttl=0 expires immediately. Reject negative TTL. Replacing and deleting entries must work; reads do not extend expiry.",
         'def process(data):\n    return [None for _ in data]',
         '''def process(data):
             cache = {}; results = []
             for operation in data:
                 kind, key, now = operation["op"], operation["key"], operation["now"]
                 if kind == "set":
                     if operation["ttl"] < 0: raise ValueError("negative ttl")
                     cache[key] = (operation["value"], now + operation["ttl"]); results.append(None)
                 elif kind == "delete": cache.pop(key, None); results.append(None)
                 elif kind == "get":
                     entry = cache.get(key); results.append(entry[0] if entry and now < entry[1] else None)
                 else: raise ValueError("unknown operation")
             return results''',
         [([{"op": "set", "key": "a", "value": 7, "now": 0, "ttl": 2}, {"op": "get", "key": "a", "now": 1}, {"op": "get", "key": "a", "now": 2}], [None, 7, None]), ([{"op": "set", "key": "x", "value": 8, "now": 0, "ttl": 0}, {"op": "get", "key": "x", "now": 0}], [None, None]), ([{"op": "set", "key": "x", "value": 1, "now": 0, "ttl": 9}, {"op": "set", "key": "x", "value": 2, "now": 1, "ttl": 9}, {"op": "get", "key": "x", "now": 2}, {"op": "delete", "key": "x", "now": 3}, {"op": "get", "key": "x", "now": 4}], [None, None, 2, None, None]), ([], [])], tags=("held-out", "larger-autonomy")),
    task("atomic-patches", "Apply a list of top-level set/delete operations to document. Return {document, original}, preserving original input. Validate the entire patch before applying: set requires value, delete requires existing key at that step, unknown operations or absent keys reject with ValueError. Never modify original even on error.",
         'def process(data):\n    return {"document":data["document"], "original":data["document"]}',
         '''import copy
         def process(data):
             result = copy.deepcopy(data["document"])
             for operation in data["patch"]:
                 key = operation["key"]
                 if operation["op"] == "set": result[key] = operation["value"]
                 elif operation["op"] == "delete" and key in result: del result[key]
                 else: raise ValueError("invalid patch")
             return {"document": result, "original": data["document"]}''',
         [({"document": {"a": 1}, "patch": [{"op": "set", "key": "b", "value": [2]}, {"op": "delete", "key": "a"}]}, {"document": {"b": [2]}, "original": {"a": 1}}), ({"document": {}, "patch": [{"op": "delete", "key": "x"}]}, {"error": True}), ({"document": {}, "patch": []}, {"document": {}, "original": {}})], tags=("held-out", "multiple-criteria")),
    task("stream-deduplication", "Given event objects with id and payload, return only the first event for each id in original order. IDs may be strings or integers, and the integer 1 must be distinct from string '1'. Retain complete objects and accept empty input.",
         'def process(data):\n    return data',
         '''def process(data):
             seen = set(); result = []
             for event in data:
                 key = (type(event["id"]), event["id"])
                 if key not in seen: seen.add(key); result.append(event)
             return result''',
         [([{"id": 1, "payload": "a"}, {"id": "1", "payload": "b"}, {"id": 1, "payload": "c"}], [{"id": 1, "payload": "a"}, {"id": "1", "payload": "b"}]), ([], [])],
         alternative='''def process(data):
             return [event for i, event in enumerate(data) if not any(type(previous["id"]) is type(event["id"]) and previous["id"] == event["id"] for previous in data[:i])]''', tags=("held-out", "alternative")),
    task("sliding-rate-limit", "Input limit is a positive integer, window is positive, timestamps are nondecreasing numeric times. Accept requests only if fewer than limit previously accepted timestamps are in (now-window, now]; rejected requests don't consume capacity. Return booleans. Reject nonpositive limit/window or decreasing timestamps.",
         'def process(data):\n    return [True for _ in data["timestamps"]]',
         '''from collections import deque
         def process(data):
             limit, window, times = data["limit"], data["window"], data["timestamps"]
             if type(limit) is not int or limit <= 0 or window <= 0 or any(a > b for a, b in zip(times, times[1:])): raise ValueError("bad limiter")
             accepted = deque(); results = []
             for now in times:
                 while accepted and accepted[0] <= now-window: accepted.popleft()
                 allow = len(accepted) < limit; results.append(allow)
                 if allow: accepted.append(now)
             return results''',
         [({"limit": 2, "window": 10, "timestamps": [0, 0, 1, 9, 10, 10, 10]}, [True, True, False, False, True, True, False]), ({"limit": 1, "window": 1, "timestamps": [0, .5, 1]}, [True, False, True]), ({"limit": 0, "window": 1, "timestamps": []}, {"error": True}), ({"limit": 1, "window": 1, "timestamps": [2, 1]}, {"error": True})], tags=("held-out", "long-tail")),
    task("schema-migration", "Migrate a list of records from v1 {version:1, full_name, ...} to v2 {version:2, name:{display:full_name}, ...}. Preserve unrelated fields, don't mutate originals, leave v2 records unchanged, and be idempotent. Reject unknown versions, missing/nonstring v1 full_name, and existing v1 name collisions. Return {records, original}.",
         'def process(data):\n    return {"records":data,"original":data}',
         '''import copy
         def process(data):
             result = copy.deepcopy(data)
             for row in result:
                 if row.get("version") == 2: continue
                 if row.get("version") != 1 or not isinstance(row.get("full_name"), str) or "name" in row: raise ValueError("invalid record")
                 row["name"] = {"display": row.pop("full_name")}; row["version"] = 2
             return {"records": result, "original": data}''',
         [([{"version": 1, "full_name": "Åse", "id": 7}, {"version": 2, "name": {"display": "Bob"}}], {"records": [{"version": 2, "name": {"display": "Åse"}, "id": 7}, {"version": 2, "name": {"display": "Bob"}}], "original": [{"version": 1, "full_name": "Åse", "id": 7}, {"version": 2, "name": {"display": "Bob"}}]}), ([{"version": 1, "full_name": "x", "name": {}}], {"error": True}), ([{"version": 3}], {"error": True}), ([{"version": 2, "name": {"display": "Åse"}}], {"records": [{"version": 2, "name": {"display": "Åse"}}], "original": [{"version": 2, "name": {"display": "Åse"}}]})], tags=("held-out", "larger-autonomy")),
    task("inventory-transactions", "Simulate inventory from initial nonnegative integer stock and batches of {sku, delta} integer changes. Apply each batch atomically if all SKUs exist and final quantities after the whole batch are nonnegative; otherwise reject that batch, retain stock, and continue. Repeated SKU deltas aggregate before checking. Return {stock, accepted} with booleans per batch. Reject invalid initial stock or noninteger deltas (bool invalid).",
         'def process(data):\n    return {"stock": data["stock"], "accepted": [False for _ in data["batches"]]}',
         '''def process(data):
             stock = dict(data["stock"]); accepted = []
             if any(type(v) is not int or v < 0 for v in stock.values()): raise ValueError("invalid stock")
             for batch in data["batches"]:
                 next_stock = dict(stock); valid = True
                 for change in batch:
                     key, delta = change["sku"], change["delta"]
                     if type(delta) is not int: raise ValueError("invalid delta")
                     if key not in next_stock: valid = False
                     else: next_stock[key] += delta
                 valid = valid and all(v >= 0 for v in next_stock.values())
                 accepted.append(valid)
                 if valid: stock = next_stock
             return {"stock": stock, "accepted": accepted}''',
         [({"stock": {"a": 2, "b": 0}, "batches": [[{"sku": "a", "delta": -3}, {"sku": "a", "delta": 2}], [{"sku": "a", "delta": -2}, {"sku": "b", "delta": 9}], [{"sku": "a", "delta": 1}]]}, {"stock": {"a": 2, "b": 0}, "accepted": [True, False, True]}), ({"stock": {"a": 1}, "batches": [[{"sku": "x", "delta": 1}], []]}, {"stock": {"a": 1}, "accepted": [False, True]}), ({"stock": {"a": -1}, "batches": []}, {"error": True})], tags=("held-out", "larger-autonomy", "repair-heavy")),
]

# Public standards information is task context for every arm, never private probe inputs/results.
STANDARD_REFERENCES = {
    'unicode-usernames': '''Public reference: https://www.unicode.org/Public/18.0.0/ucd/PropList.txt
Unicode White_Space consists of U+0009 through U+000D, U+0020, U+0085, U+00A0,
U+1680, U+2000 through U+200A, U+2028, U+2029, U+202F, U+205F and U+3000.
Python documents its string whitespace predicate using general category Zs or
bidirectional classes WS, B or S. These definitions need not be identical.
Python reference: https://docs.python.org/3.14/library/stdtypes.html#str.isspace
These public facts explain the named domain; the original request remains binding.
''',
    'utc-timestamps': '''Public reference: https://science.data.nasa.gov/fits/documentation/iso-time
ISO date representations include calendar dates (YYYY-MM-DD), compact calendar
dates (YYYYMMDD), week dates (YYYY-Www-D or YYYYWwwD), and ordinal dates
(YYYY-DDD or YYYYDDD). Ordinal numbering starts at 001 and follows the Gregorian
leap-year rules. Combined date/time values use T. Time can omit its colons;
seconds or minutes can be omitted when less precision is needed. Fractional
seconds use a dot or comma. Midnight at the end of a date can be written 24:00
when minutes and seconds are zero; it denotes the next day's 00:00. UTC uses Z;
offsets use signed hours, hours/minutes, or hours:minutes. A positive offset
means local time is ahead of UTC. This public overview is not the entire standard
and does not narrow the original request. It contains no benchmark test inputs
or expected outputs.
''',
}
for item in TASKS:
    if item['id'] in STANDARD_REFERENCES:
        item['files'] = {'REFERENCES.md': STANDARD_REFERENCES[item['id']]}
    if item['id'] == 'stable-pagination':
        item['library_integer_fields'] = ['offset', 'limit']


def source(item):
    return (f'# Request: {item["id"]}\n\nImplement this change in the existing JSON CLI product.\n\n'
            f'R1: {item["requirement"]}\n\n'
            'R2: Keep the existing app.py JSON command interface: one JSON argument, successful JSON on stdout and exit 0; ValueError/KeyError/TypeError produce exit 2, an explanation on stderr, and no stdout. --version still prints pilot-tool 1.0 and exits 0. Existing argument errors remain errors.\n\n'
            'R3: Standard library only. No network, external effects, or input/source mutation. Preserve the CLI version and public product.process(data) entry point. Implementation architecture and additional local tests are your choice.\n')


def brief(item):
    return '# Source-grounded brief\n\n| ID | Required observable outcome |\n|---|---|\n' + ''.join(
        f'| R{i} | {paragraph.split(": ", 1)[1]} |\n'
        for i, paragraph in enumerate([line for line in source(item).splitlines() if line.startswith(('R1:', 'R2:', 'R3:'))], 1))


def contract(item):
    rows = [line.split(': ', 1) for line in source(item).splitlines() if line.startswith(('R1:', 'R2:', 'R3:'))]
    return (f'# Acceptance contract: {item["id"]}\n\nContract revision: v1\nSource: [Original request](source.md)\nParent: None\nPrerequisites: None\nIntended outcome: Fulfill the complete original JSON CLI request.\n\n## Acceptance matrix\n\n'
            '| ID | Source | Requirement | Boundaries / counterexamples | Seam | Oracle | Planned evidence | Plan state |\n|---|---|---|---|---|---|---|---|\n'
            + ''.join(f'| {ident} | Original request {ident} | {requirement} | Source-defined boundaries | Public CLI | Original source expectations | Execute discriminating public probes | planned |\n' for ident, requirement in rows)
            + '\n## Unresolved gaps\n\nNone.\n\n## Open questions\n\nNone.\n\n## Out of scope\n\nExternal effects and dependencies.\n\n## Change notes\n\nInitial synthetic benchmark agreement, scoped to local experiments; no historical approval asserted.\n')

"""Frozen public requests and worker-only seed generation for the vNext study.

The seed contains NO grader, reference, alternative, defect, or expected answer.
"""
from pathlib import Path

TASKS = {
    "collision-slugs": """Implement app.process(payload) for JSON {"titles": [strings]}.
Return {"slugs": [strings]} in original order. Normalize each title by
lowercasing and replacing every run of characters outside ASCII a-z and 0-9
with one hyphen; trim end hyphens. Empty normalized titles are invalid.
Every final slug must be unique: if its base is already taken, append
-2, -3, etc., choosing the first unused name globally. Treat numbers and
suffixes in original titles just like any other normalized base.
Reject invalid payloads with ValueError. Preserve service.handle, the JSON
stdin/stdout CLI, and the existing exact --version response; do not change
their files. Focused regression tests are recommended, not part of the scored behavior.""",

    "ordered-inventory": """Implement app.process(payload) for
{"starting": {"sku": nonnegative integer}, "events": [
{"sku": nonempty string, "delta": integer}, ...]}.
Apply events in the order given, starting unseen SKU quantities at zero.
A transient negative stock is invalid even if later events restore it.
Return {"stock": {"sku": quantity}} containing all starting and visited SKUs,
including zeros. Reject malformed records, booleans masquerading as integers,
and any negative intermediate stock with ValueError. Preserve service.handle,
the JSON CLI and exact --version response without modifying their files.
Focused regression tests are recommended, not part of the scored behavior.""",

    "half-open-union": """Implement app.process(payload) for
{"intervals": [[start, end], ...]} with integer coordinates from 0 through
200 inclusive and start <= end. Intervals are half-open [start, end):
zero-length intervals contribute nothing. Sort and merge all overlapping
OR touching nonempty intervals; return {"segments": [[start, end], ...],
"covered": total_integer_length}. Reject malformed or out-of-range intervals,
including boolean coordinates, with ValueError. Preserve service.handle,
the JSON CLI and exact --version response without modifying their files.
Focused regression tests are recommended, not part of the scored behavior.""",

    "form-multimap": """Implement app.process(payload) for
{"query": string}, an application/x-www-form-urlencoded query without '?':
split on '&', ignore empty segments, split each nonempty segment at the
FIRST '=' (missing '=' means empty value), decode '+' as space and percent
escapes as UTF-8 bytes. Reject malformed '%' escapes, invalid UTF-8, and
empty decoded field names with ValueError. Repeated field names retain
their values in occurrence order. Return {"fields": {"name": ["value", ...]}}.
Accept plain Unicode characters as well as percent-escaped UTF-8.
Preserve service.handle, the JSON CLI and exact --version response without
modifying their files. Focused regression tests are recommended, not part of the scored behavior.""",

    "largest-remainder": """Implement app.process(payload) for
{"units": nonnegative integer <= 1000, "weights": [nonnegative integers]}.
Weights must have length 1..10 and at least one strictly positive member.
Allocate all units proportionally using exact integer arithmetic: first
floor(units*weight/sum(weights)), then distribute remaining units to the
largest fractional remainders, breaking ties by EARLIER index; each index
may get at most one remainder unit. Return {"allocations": [integers]}.
Reject malformed values, including booleans as numbers, with ValueError.
Preserve service.handle, JSON CLI and exact --version response without
modifying their files. Focused regression tests are recommended, not part of the scored behavior.""",

    "four-way-islands": """Implement app.process(payload) for
{"grid": [strings]}: a nonempty rectangular grid of '.' (water) and
'#' (land). Land cells connect ONLY vertically and horizontally, not on
diagonals. Return {"count": integer, "sizes": [sizes of connected components
in descending order]}. Reject empty, jagged, non-string or invalid-character
grids with ValueError. Preserve service.handle, the JSON CLI and the exact
--version response without modifying their files. Focused regression tests are recommended, not scored.""",
}

APP_STUB = """def process(payload):
    raise NotImplementedError("Implement the entire source.md task.")
"""

SERVICE = """import app


def handle(payload):
    return app.process(payload)
"""

CLI = """import json
import sys
import app


def main():
    if sys.argv[1:] == ["--version"]:
        print("api-v1")
        return 0
    if sys.argv[1:]:
        print("ERROR: unsupported arguments", file=sys.stderr)
        return 2
    try:
        value = app.process(json.load(sys.stdin))
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, NotImplementedError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
"""

COMPAT = """import pathlib
import subprocess
import sys
import unittest


class Compatibility(unittest.TestCase):
    def test_existing_version_flag(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py"),
                                 "--version"], cwd=repo,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, "api-v1\\n", ""))
"""


def seed(task_id, output):
    """Prepare one ordinary-agent assignment without distributing answer keys."""
    if task_id not in TASKS:
        raise ValueError("Unknown frozen task")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Assignments are write-once; choose a new directory")
    output.mkdir(parents=True)
    (output / "source.md").write_text(TASKS[task_id], encoding="utf-8")
    product = output / "product"
    (product / "tests").mkdir(parents=True)
    for path, content in {
        "app.py": APP_STUB,
        "service.py": SERVICE,
        "cli.py": CLI,
        "README.md": ("# " + task_id + "\n\nImplement the full request in "
                      "../source.md while retaining the existing interfaces.\n"),
        "tests/test_compat.py": COMPAT,
    }.items():
        (product / path).write_text(content, encoding="utf-8")
    return product

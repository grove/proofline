# Source acceptance and grading notes (declared before dispatch)

Task 1: [python-dotenv #715](https://github.com/theskumar/python-dotenv/issues/715).
The complete title/body and comments are in `requests/`. Baseline:
`0b2880591780a426b0551436f47a17e7a76d954f`.

- `${b:-d}` uses `d` for an empty `b` and a missing `b`.
- A populated `b=c` stays `c`; `${b}` without a default stays empty.
- Preserve ordinary parsing and interpolation behavior; add a regression.
- Either fixing shared variable resolution or another equivalent public-path fix
  is valid. No exception class, internal helper, or treatment of `None` is imposed
  by this request. Those unspecified choices are not private failure conditions.

Relevant existing tests: `tests/test_variables.py`, interpolation cases in
`tests/test_main.py` (`test_dotenv_values_string_io`), and full `tests/`.
Suggested ordinary command: `PYTHONPATH=src python -m pytest tests/test_variables.py tests/test_main.py`.

Task 2: [humanize #366](https://github.com/python-humanize/humanize/issues/366).
Baseline: `785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b`.

- The complete original reproducer returns `Size: 976.6K`.
- Custom formatters with prefixes and suffixes remain usable, including negative
  sizes. Do not require the whole formatted string to be numeric.
- Preserve ordinary numeric formatting and existing decimal/binary/GNU rollover
  cases. Add regression coverage for prefix and suffix text.
- Both explicitly proposed alternatives are valid: skip rollover for nonnumeric
  decorated strings, or derive numeric rounding independently. At a decorated
  rollover boundary, both `Size: 1000.0 kB` and `Size: 1.0 MB` are accepted.
- No particular parser, exception class, new API, or unrelated locale fix is
  required. Unspecified/malformed format behavior is not independently graded.

Relevant existing tests: `tests/test_filesize.py`, particularly its six rollover
cases and negative counterparts. Ordinary command:
`PYTHONPATH=src python -m pytest tests/test_filesize.py`.

Both attempts must deliver a code change, useful regression coverage, actual
self-testing where supported, and a handoff identifying changed files, commands,
results and unresolved issues. A claimed completion or green sampled tests alone
cannot establish whole-task correctness. Review the final diff against the whole
request after protected behavioral probes. If an alternative defeats a probe
without violating the source, record a disputed expectation and leave judgment
pending rather than manufacturing a defect.

The independent probes are finite behavioral samples, authored by the organizer
before worker dispatch. They are independent of coding attempts, not independent
human replication. `probe_humanize.py` loads the actual filesize/i18n modules
without package initialization because the source checkout lacks hatch-generated
`_version.py`; public package installation is not certified by that probe.

The current host has no pytest. Do not replace it with a fake pytest runner or
weaken isolation. Workers may use stdlib assertions and must report unavailable
ordinary tests. Full-suite status remains UNKNOWN unless actually executed.

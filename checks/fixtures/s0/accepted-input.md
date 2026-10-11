# Accepted direct brief — username validation

Source: `source.md` in this fixture. This brief expresses every original source
obligation; the source remains authoritative. The host harness must freeze and
record the exact bytes of both files alongside the base and candidate identity.

| ID | Required observable result |
| --- | --- |
| U1 | Empty and whitespace-only usernames, including Unicode whitespace, fail with status `2`, empty stdout, and stderr containing `username must not be empty or whitespace-only`. |
| U2 | Every nonblank command-line username succeeds with status `0`, empty stderr, and a JSON object containing only `username` with the exact original string, including any surrounding whitespace. |
| U3 | The single positional argument, `--` terminator, `-h`/`--help`, and missing/extra-argument usage errors retain their existing behavior. |
| U4 | The command stays a local standard-library Python 3 CLI, adds no file or network effects, and has no new dependencies. |

Implementation choices and JSON formatting are not acceptance requirements.
Existing test commands and suggested observation paths are useful starting
points, not proof that every obligation is satisfied.

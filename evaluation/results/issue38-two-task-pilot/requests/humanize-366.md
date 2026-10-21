`naturalsize()` raises `ValueError` for custom format strings with text

## Environment

- humanize 4.16.0 and current `main` at `42b4a1db`
- Python 3.11.15

## Reproduction

```python
import humanize

print(humanize.naturalsize(999_999, gnu=True, format="Size: %.1f"))
```

humanize 4.15.0 returns:

```text
Size: 976.6K
```

humanize 4.16.0 and current `main` raise:

```text
ValueError: could not convert string to float: 'Size: 976.6'
```

## Expected behavior

The documented custom formatter should continue to accept text around the numeric conversion.
Since this behavior worked in 4.15.0, preserving it would avoid a backward compatibility regression.

## Cause

PR #329 added unit rollover handling. The new condition formats the mantissa with the
user-provided format and passes the entire result to `float()`:

```python
float(format % (abs_bytes / (base**exp)))
```

This works for a plain numeric format such as `"%.1f"`, but not for a general formatter
such as `"Size: %.1f"`.

## Suggested fix

It might be preferable not to require the complete user-formatted result to be parseable as a float. One
backward-compatible option is to apply rollover only when the formatted result is a
plain numeric string, and otherwise preserve the pre-4.16 behavior. A more complete
solution could derive the rounded numeric mantissa independently from surrounding text.

It might also be worth adding a regression test covering both a prefix and a suffix.

## How this was found

This was found by change-directed differential testing: reviewing the recent rollover change, mapping it to the public `naturalsize() API`, and constructing a documented custom formatter that reaches the newly added `float(format % value)` expression.

Related: #329, which fixes rollover but does not discuss custom format strings.

Thanks for taking the time to review this report! I appreciate all the work that goes into maintaining this project.

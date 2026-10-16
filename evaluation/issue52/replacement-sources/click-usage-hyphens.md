# `HelpFormatter.write_usage` breaks options at a hyphen

If an option containing a hyphen in its name is printed at the line break limit, it’s broken at the hyphen.

### Reproduction

```python
import click

options = [
    "--enable-verbose-logging",
    "--output-file-path",
    "--max-retry-count",
    "--disable-cache-mode",
    "--config-file-location",
    "--user-auth-token",
    "--auto-update-interval",
    "--force-overwrite-existing",
    "--network-timeout-seconds",
    "--debug-trace-enabled",
]

f = click.HelpFormatter(width=65)
f.write_usage("program", " ".join(options))
print(f.getvalue())
```

### Expected output
```
Usage: program --enable-verbose-logging --output-file-path
               --max-retry-count --disable-cache-mode
               --config-file-location --user-auth-token
               --auto-update-interval --force-overwrite-existing
               --network-timeout-seconds --debug-trace-enabled
```

### Actual output
```
Usage: program --enable-verbose-logging --output-file-path --max-
               retry-count --disable-cache-mode --config-file-
               location --user-auth-token --auto-update-interval
               --force-overwrite-existing --network-timeout-
               seconds --debug-trace-enabled
```

### Environment

- Python version: 3.12.3
- Click version: 8.3.1

### Additional information

#### `width` option

This also happens without specifying `width`. The `width` option is altered in the example to make the issue more frequent.

#### Relevance to other use cases

This may likely only affect:

- direct users of `click.HelpFormatter`,
- users of `click.argument` with custom `metavar` containing hyphens. 

On the other hand, `click` prints `[OPTIONS]` instead of listing individual options on the usage line and uses underscores instead of hyphens in argument names (unless specifying `metavar`).

#### Cause

I looked into the code and found that `textwrap.TextWrapper` is used under the hood, which has the [`break_on_hyphens`](https://docs.python.org/3/library/textwrap.html#textwrap.TextWrapper.break_on_hyphens) option. However, there is no option for the `click` user to influence this, apart from reimplementing `HelpFormatter.write_usage` (in a subclass) and `wrap_text`.

## Captured comment: ThiefMaster — 2026-09-17T23:54:52Z

https://github.com/pallets/click/issues/3362#issuecomment-5722823230

@Pitchfork-and-Torch It is not acceptable to let LLM agents open issues/PRs autonomously - https://palletsprojects.com/contributing/llm-ai

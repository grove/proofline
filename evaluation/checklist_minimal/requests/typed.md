missing py.typed file

IMO the code has enough type hints to consider this package typed, so we should add a `py.typed` file to make mypy not complain about missing stubs. Current situation, with `import schedule` on line 15 of `my_project/__main__.py`:

```
$ mypy my_project/
my_project/__main__.py:15: error: Skipping analyzing "schedule": found module but no type hints or library stubs
my_project/__main__.py:15: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
Found 1 error in 1 file (checked 10 source files)
```
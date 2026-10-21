An empty value ignores ${name:-default}

`${name:-default}` is the POSIX form that uses the default when `name` is unset or empty. An empty value is returned as itself.

```python
dotenv.dotenv_values(stream=io.StringIO("b=\na=${b:-d}"))
# {'b': '', 'a': ''}
```

`a` should be `d`. A missing `b` already becomes `d`. `b=c` still stays `c`. `${b}` with no default stays empty.

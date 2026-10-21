funcutils.wraps drops positional-only parameters from generated signatures

`funcutils.wraps` drops the `/` marker when compiling a wrapper, so a positional-only parameter becomes positional-or-keyword. This breaks valid calls that reuse the parameter name inside `**kwargs`.

Reproduced on upstream `master` at `961dcff3f42e73b245aef65e377fe82763b257bb`:

```python
from boltons.funcutils import wraps

def original(a, /, **kw):
    return a, kw

@wraps(original)
def wrapped(*args, **kwargs):
    return original(*args, **kwargs)

print(original(1, a=2))  # (1, {'a': 2})
print(wrapped(1, a=2))   # TypeError: original() got multiple values for argument 'a'
```

The wrapped call should return the same result as the original. Its generated source is currently:

```python
def original(a, **kw):
    return _call(a, **kw)
```

`FunctionBuilder.from_func(original)` records `posonlyargs == ['a']`, but `get_sig_str()` does not pass that information to the signature formatter. The argument collision happens before the wrapper body runs. The existing positional-only regression checks forwarding of positional calls and does not cover this collision.

#425 and #445 address argument forwarding; this concerns the generated function's calling signature.

AI assistance: this issue was prepared with an AI coding tool.


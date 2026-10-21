import inspect
import json
from boltons.funcutils import FunctionBuilder, wraps

cases = []
def check(label, run):
    try:
        run()
        cases.append({"label": label, "passed": True})
    except Exception as error:
        cases.append({"label": label, "passed": False, "error": repr(error)})

def collision():
    def original(a, /, **kw):
        return a, kw
    @wraps(original)
    def wrapped(*args, **kwargs):
        return original(*args, **kwargs)
    assert wrapped(1, a=2) == original(1, a=2)
    assert inspect.signature(wrapped, follow_wrapped=False).parameters['a'].kind == inspect.Parameter.POSITIONAL_ONLY

def mixed():
    def original(a: int, b=2, /, c=3, *args, flag=True, **kw):
        return a, b, c, args, flag, kw
    @wraps(original)
    def wrapped(*args, **kwargs):
        return original(*args, **kwargs)
    assert wrapped(1, b=9, a=8) == original(1, b=9, a=8)
    assert wrapped(1, 4, 5, 6, flag=False, a=9) == original(1, 4, 5, 6, flag=False, a=9)
    assert '/' in FunctionBuilder.from_func(original).get_sig_str(with_annotations=False)

def reject_keyword():
    def original(a, /):
        return a
    @wraps(original)
    def wrapped(*args, **kwargs):
        return original(*args, **kwargs)
    try:
        wrapped(a=1)
    except TypeError:
        pass
    else:
        raise AssertionError('positional-only keyword accepted')

def ordinary():
    def original(a, b=2, *, c=3):
        return a, b, c
    @wraps(original)
    def wrapped(*args, **kwargs):
        return original(*args, **kwargs)
    assert wrapped(a=1, b=4, c=5) == (1, 4, 5)

def positional_default():
    def original(a=1, /, **kw):
        return a, kw
    @wraps(original)
    def wrapped(*args, **kwargs):
        return original(*args, **kwargs)
    assert wrapped() == (1, {})
    assert wrapped(a=9) == (1, {'a': 9})

check('original-collision', collision)
check('mixed-defaults-varargs-annotations', mixed)
check('keyword-rejection', reject_keyword)
check('ordinary-signature-compatibility', ordinary)
check('positional-default-without-varargs', positional_default)
print(json.dumps({'cases': cases}))
assert all(c['passed'] for c in cases)

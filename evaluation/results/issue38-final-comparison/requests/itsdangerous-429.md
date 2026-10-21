`URLSafeSerializer.loads` silently ignores unexpected `max_age` argument

This report considers only the `loads` method of the `URLSafeSerializer` type.
The "problematic" behavior described below can probably be applied to other methods and types as well;
but for the sake of simplicity, I will keep the scope limited.

---
**_The Example_**

I will illustrate my problem with the following code snippet.
This code is not the problematic one.
It works as expected and fails when loading the signed string.

```python
import itsdangerous

serializer = itsdangerous.URLSafeTimedSerializer("SECRET")
signed = serializer.dumps("value")
serializer.loads(signed, max_age=-1)  # !!
```

Now, let's switch to an _untimed_ serializer:

```diff
import itsdangerous

- serializer = itsdangerous.URLSafeTimedSerializer("SECRET")
+ serializer = itsdangerous.URLSafeSerializer("SECRET")
signed = serializer.dumps("value")
serializer.loads(signed, max_age=-1)  # !!
```

---

**_What should happen here?_**

I would still expect some kind of error or a warning on the line with `loads`;
perhaps a `TypeError` like:

```
TypeError: URLSafeSerializer.loads() got an unexpected keyword argument 'max_age'
```

Furthermore, the type checkers should warn the developer before they even run the code.

---

**_What actually happens_**

This code runs without _any_ errors.
`max_age` is silently ignored.

Pyright (the type checker) is totally happy with the code.

---

**_What is the big deal?_**

I think this behavior can lead to **security issues**.
I can totally see my self accidentally making such a change in a codebase.
As a result, for example, expired tokens may be accepted forever.

---

Environment:

- Python version: 3.14.2
- ItsDangerous version: 2.2.0


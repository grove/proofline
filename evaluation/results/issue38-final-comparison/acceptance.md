# Frozen source obligations and review scope

The full public issue title/body and discussion captures are in `requests/`.
Both selected issues had no comments. No earlier Proofline coding assignment
used either request; public implementation or training exposure is UNKNOWN.
This does not assert that the tasks are globally unseen.

## Boltons #510

The original explicitly says the wrapped call should return the same result as
the original and identifies the missing `/` in the generated calling signature.
Accept a fix in the formatter, the builder, or another equivalent shared path.
Do not require a particular helper signature or code shape.

The frozen behavioral sample checks the exact `wrapped(1, a=2)` reproducer,
the actual generated signature with `follow_wrapped=False`, mixed positional
defaults, varargs, annotations, keyword-only parameters and repeated names in
`**kwargs`. A separate positional default without varargs protects against
incorrectly forwarding that default by keyword. A positional-only argument
without `**kwargs` must reject a keyword call. Ordinary signatures must still
work. Existing funcutils tests and the available whole suite supply broader
compatibility evidence. Source/test review checks callers and default handling.

This is a shared signature-generation change with regression files, not a
request to rewrite FunctionBuilder, add unrelated callable support, or redesign
the library. Such extra requirements are not grading criteria.

## ItsDangerous #429

The original explicitly limits the report to `URLSafeSerializer.loads`. It
asks for some error **or warning** when `max_age` is passed, and asks type
checkers to flag that call. No particular exception class or message is
required. A runtime-only fix is insufficient. Removing ignored `**kwargs`,
or a properly typed rejecting/warning path, can satisfy the request.

The frozen sample checks the exact unexpected `max_age=-1` case. It also checks
that the timed serializer still rejects expired tokens and accepts unexpired
tokens and `return_timestamp`; normal untimed round trips, salts, key lists,
unsafe inspection and invalid-signature rejection remain supported. These are
compatibility guards against fixing the report by disabling signed loading or
timed features, not new product features. Pyright must diagnose the untimed
argument while accepting ordinary untimed and documented timed calls. Diagnostic
wording is not prescribed. Existing tests and review cover inheritance/callers.

## Qualification and alternatives

The existing `evaluation.source_preflight.qualify` binds declarations to exact
request and probe bytes. Before dispatch, the existing native protected command
runner observed baseline/reference/alternative/defective controls for each task.
Both references and plausible alternatives pass; both original baselines and
deliberate defects fail. The Boltons defect misforwards positional defaults;
the ItsDangerous defect rejects at runtime but leaves typing permissive.

The first no-model preparation pass found two fixture gaps: the Boltons defect
was not triggered by a sample that always had varargs, and `typing.Never` was
unavailable for the explicitly selected Python 3.10 typing target. The final
pre-dispatch checks add the no-varargs default case and use `typing.NoReturn`
in the alternative control. Pyright's interpreter path was pinned to avoid
Apple discovery-shim noise. First-pass evidence is retained separately. These
were preparation corrections, with zero coding attempts or model feedback.

All candidate assessments use the same frozen checks. Passing tests alone is
not acceptance. The organizer reviews terminal diffs against these requests
independently of each worker context; this is not an independent human review
or an extra reviewer-model stage. No grading feedback or repairs are supplied
to either arm. Unexpected behavior beyond these source obligations is reported
as a limitation or observation, not silently converted into a new failure rule.

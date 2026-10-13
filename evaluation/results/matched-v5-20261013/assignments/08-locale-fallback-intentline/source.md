Implement per-key translations for {"catalog": {locale: {key: text}},
"locales": [locale, ...], "keys": [key, ...], "default": locale}.
Locale names and keys are nonempty strings; translations are strings, including
empty strings. For EACH key, try requested locales in order, trying each exact
locale then repeatedly removing its last hyphen subtag. Only if no requested
locale contains that key, try the exact default locale (no default truncation).
Return {"texts": [translation_or_null, ...]} in keys order, retaining duplicates.
Matching is case sensitive; an empty translation is a found value, not missing.
Reject malformed containers/values with ValueError. Empty keys/locales/catalog
containers are allowed. Do not impose a BCP-47 grammar beyond nonempty strings.

Expose the same behavior through app.process, service.handle and the existing
JSON stdin/stdout CLI. Add service.batch(payloads): return each process result
in input order; reject a non-list or any invalid member with ValueError.
Do not mutate any input, including on errors. Preserve the exact CLI --version
response and unsupported-argument behavior; keep cli.py unchanged. Extra object
keys are allowed. Update a stale test expectation if it contradicts this request.

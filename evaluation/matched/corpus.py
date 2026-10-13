"""Four fresh requests, literal independent expectations, and trusted controls.

Workers receive only source.md and the seed, never this file.
"""
from pathlib import Path

from evaluation.v1 import tasks as v1

COMMON = """
Expose the same behavior through app.process, service.handle and the existing
JSON stdin/stdout CLI. Add service.batch(payloads): return each process result
in input order; reject a non-list or any invalid member with ValueError.
Do not mutate any input, including on errors. Preserve the exact CLI --version
response and unsupported-argument behavior; keep cli.py unchanged. Extra object
keys are allowed. Update a stale test expectation if it contradicts this request.
"""

REQUESTS = {
    "atomic-transfers": """Implement transfers for {"balances": {name: integer >= 0},
"transfers": [[from, to, amount], ...]}. Names are nonempty strings; amount is
a nonnegative integer. Booleans are invalid numbers. Both accounts must exist.
Apply transfers in order; reject insufficient funds at any intermediate step,
including a self-transfer exceeding that account's balance. Return
{"balances": final_balances}. No partial result on rejection.
""" + COMMON,
    "locale-fallback": """Implement per-key translations for {"catalog": {locale: {key: text}},
"locales": [locale, ...], "keys": [key, ...], "default": locale}.
Locale names and keys are nonempty strings; translations are strings, including
empty strings. For EACH key, try requested locales in order, trying each exact
locale then repeatedly removing its last hyphen subtag. Only if no requested
locale contains that key, try the exact default locale (no default truncation).
Return {"texts": [translation_or_null, ...]} in keys order, retaining duplicates.
Matching is case sensitive; an empty translation is a found value, not missing.
Reject malformed containers/values with ValueError. Empty keys/locales/catalog
containers are allowed. Do not impose a BCP-47 grammar beyond nonempty strings.
""" + COMMON,
    "dependency-order": """Implement stable dependency ordering for {"nodes": [name, ...],
"edges": [[before, after], ...]}. Names are nonempty strings and nodes unique.
Edges must reference declared nodes. Repeated identical edges have no effect.
At EACH step choose the earliest node in the ORIGINAL nodes list whose
dependencies are already emitted. Return {"order": [names]}.
Reject malformed records, self-loops and ANY cycle, including disconnected
cycles, with ValueError. Empty nodes/edges are allowed. Never sort by name.
""" + COMMON,
    "fifo-upserts": """Implement a FIFO record cache for {"capacity": integer >= 0,
"events": [{"id": nonempty_string, "value": any_JSON_value}, ...]}.
Every event must contain both id and value. Booleans are invalid capacities.
Update an existing ID in its original insertion position, without promoting it.
When inserting a new ID would exceed capacity, evict the oldest resident ID.
Capacity zero immediately evicts EVERY event. Return {"items": [final records
in FIFO order], "evicted": [IDs in eviction order, retaining repetitions]}.
Output records contain only id and value; extra input keys are ignored.
Reject malformed records/containers with ValueError. Input values may be null.
""" + COMMON,
}

# Each case has an outcome label independent of generated R inventories.
CASES = {
    "atomic-transfers": [
        ("ordered balances", {"balances": {"a": 5, "b": 0}, "transfers": [["a", "b", 3]]}, {"balances": {"a": 2, "b": 3}}),
        ("intermediate overdraft", {"balances": {"a": 1, "b": 4}, "transfers": [["a", "b", 2], ["b", "a", 2]]}, "ValueError"),
        ("self transfer funds", {"balances": {"a": 1}, "transfers": [["a", "a", 2]]}, "ValueError"),
        ("self transfer valid", {"balances": {"a": 1}, "transfers": [["a", "a", 1]]}, {"balances": {"a": 1}}),
        ("bool balance", {"balances": {"a": True}, "transfers": []}, "ValueError"),
        ("bool amount", {"balances": {"a": 2}, "transfers": [["a", "a", False]]}, "ValueError"),
        ("missing account", {"balances": {"a": 2}, "transfers": [["a", "b", 0]]}, "ValueError"),
        ("empty and extra keys", {"balances": {}, "transfers": [], "note": 1}, {"balances": {}}),
        ("malformed transfer", {"balances": {"a": 2}, "transfers": [["a", "a"]]}, "ValueError"),
        ("negative starting balance", {"balances": {"a": -1}, "transfers": []}, "ValueError"),
    ],
    "locale-fallback": [
        ("per key fallback", {"catalog": {"fr-CA": {"a": "CA"}, "fr": {"b": "FR"}, "en": {"c": "EN"}}, "locales": ["fr-CA"], "keys": ["b", "a", "c", "x", "a"], "default": "en"}, {"texts": ["FR", "CA", "EN", None, "CA"]}),
        ("empty is found", {"catalog": {"fr": {"k": ""}, "en": {"k": "E"}}, "locales": ["fr"], "keys": ["k"], "default": "en"}, {"texts": [""]}),
        ("case sensitive", {"catalog": {"fr": {"k": "F"}}, "locales": ["FR"], "keys": ["k"], "default": "en"}, {"texts": [None]}),
        ("multilevel and default exact", {"catalog": {"x": {"k": "X"}, "en": {"z": "Z"}}, "locales": ["x-y-z"], "keys": ["k", "z"], "default": "en-US"}, {"texts": ["X", None]}),
        ("no imposed locale grammar", {"catalog": {"odd_!": {"k": "ok"}}, "locales": ["odd_!"], "keys": ["k"], "default": "d"}, {"texts": ["ok"]}),
        ("empty containers", {"catalog": {}, "locales": [], "keys": [], "default": "en"}, {"texts": []}),
        ("validate unused translation", {"catalog": {"unused": {"k": 3}}, "locales": [], "keys": [], "default": "en"}, "ValueError"),
        ("invalid key", {"catalog": {}, "locales": [], "keys": [""], "default": "en"}, "ValueError"),
    ],
    "dependency-order": [
        ("original order", {"nodes": ["z", "a"], "edges": []}, {"order": ["z", "a"]}),
        ("rescan each step", {"nodes": ["a", "b", "c"], "edges": [["b", "a"]]}, {"order": ["b", "a", "c"]}),
        ("duplicate edge", {"nodes": ["a", "b"], "edges": [["a", "b"], ["a", "b"]]}, {"order": ["a", "b"]}),
        ("disconnected cycle", {"nodes": ["a", "b", "c"], "edges": [["b", "c"], ["c", "b"]]}, "ValueError"),
        ("self loop", {"nodes": ["a"], "edges": [["a", "a"]]}, "ValueError"),
        ("undeclared endpoint", {"nodes": ["a"], "edges": [["a", "b"]]}, "ValueError"),
        ("duplicate nodes", {"nodes": ["a", "a"], "edges": []}, "ValueError"),
        ("empty and extra keys", {"nodes": [], "edges": [], "note": 1}, {"order": []}),
        ("malformed edge", {"nodes": ["a"], "edges": [["a"]]}, "ValueError"),
    ],
    "fifo-upserts": [
        ("updates do not promote", {"capacity": 2, "events": [{"id": "a", "value": 1}, {"id": "b", "value": 2}, {"id": "a", "value": 3}, {"id": "c", "value": 4}]}, {"items": [{"id": "b", "value": 2}, {"id": "c", "value": 4}], "evicted": ["a"]}),
        ("zero and repeated evictions", {"capacity": 0, "events": [{"id": "a", "value": None}, {"id": "a", "value": 2}]}, {"items": [], "evicted": ["a", "a"]}),
        ("strip extra record keys", {"capacity": 1, "events": [{"id": "a", "value": [1, {"x": 2}], "note": 7}]}, {"items": [{"id": "a", "value": [1, {"x": 2}]}], "evicted": []}),
        ("bool capacity", {"capacity": False, "events": []}, "ValueError"),
        ("missing value", {"capacity": 1, "events": [{"id": "a"}]}, "ValueError"),
        ("negative capacity", {"capacity": -1, "events": []}, "ValueError"),
        ("empty id", {"capacity": 1, "events": [{"id": "", "value": 1}]}, "ValueError"),
        ("empty events", {"capacity": 3, "events": []}, {"items": [], "evicted": []}),
    ],
}

VALIDATORS = {
    "atomic-transfers": '''
    balances, events = p.get("balances"), p.get("transfers")
    if not isinstance(balances, dict) or not isinstance(events, list): raise ValueError()
    if any(not name(k) or not integer(v) or v < 0 for k,v in balances.items()): raise ValueError()
    for e in events:
        if not isinstance(e,list) or len(e)!=3: raise ValueError()
        a,b,n=e
        if not name(a) or not name(b) or a not in balances or b not in balances or not integer(n) or n<0: raise ValueError()
''',
    "locale-fallback": '''
    catalog, locales, keys, default = p.get("catalog"),p.get("locales"),p.get("keys"),p.get("default")
    if not isinstance(catalog,dict) or not isinstance(locales,list) or not isinstance(keys,list) or not name(default): raise ValueError()
    if any(not name(x) for x in locales+keys): raise ValueError()
    for loc,entries in catalog.items():
        if not name(loc) or not isinstance(entries,dict): raise ValueError()
        if any(not name(k) or not isinstance(v,str) for k,v in entries.items()): raise ValueError()
''',
    "dependency-order": '''
    nodes, edges = p.get("nodes"),p.get("edges")
    if not isinstance(nodes,list) or not isinstance(edges,list) or any(not name(x) for x in nodes): raise ValueError()
    if len(set(nodes))!=len(nodes): raise ValueError()
    for e in edges:
        if not isinstance(e,list) or len(e)!=2 or any(not name(x) or x not in nodes for x in e): raise ValueError()
''',
    "fifo-upserts": '''
    capacity, events = p.get("capacity"),p.get("events")
    if not integer(capacity) or capacity<0 or not isinstance(events,list): raise ValueError()
    if any(not isinstance(e,dict) or not name(e.get("id")) or "value" not in e for e in events): raise ValueError()
''',
}

ALGORITHMS = {
    "atomic-transfers": ('''
    stock=dict(balances)
    for a,b,n in events:
        if stock[a]<n: raise ValueError()
        stock[a]-=n; stock[b]+=n
    return {"balances":stock}
''', '''
    changes={k:0 for k in balances}
    for a,b,n in events:
        if balances[a]+changes[a]<n: raise ValueError()
        changes[a]-=n; changes[b]+=n
    return {"balances":{k:v+changes[k] for k,v in balances.items()}}
'''),
    "locale-fallback": ('''
    texts=[]
    for key in keys:
        found=False
        for locale in locales:
            while locale:
                if key in catalog.get(locale,{}):
                    texts.append(catalog[locale][key]); found=True; break
                locale=locale.rsplit("-",1)[0] if "-" in locale else ""
            if found: break
        if not found: texts.append(catalog.get(default,{}).get(key))
    return {"texts":texts}
''', '''
    chain=[]
    for locale in locales:
        parts=locale.split("-")
        chain.extend("-".join(parts[:i]) for i in range(len(parts),0,-1))
    chain.append(default)
    return {"texts":[next((catalog[loc][k] for loc in chain if k in catalog.get(loc,{})),None) for k in keys]}
'''),
    "dependency-order": ('''
    pending=list(nodes); done=[]
    while pending:
        ready=next((x for x in pending if all(a in done for a,b in edges if b==x)),None)
        if ready is None: raise ValueError()
        pending.remove(ready); done.append(ready)
    return {"order":done}
''', '''
    incoming={n:set() for n in nodes}; outgoing={n:set() for n in nodes}
    for a,b in edges: incoming[b].add(a); outgoing[a].add(b)
    done=[]
    while len(done)<len(nodes):
        ready=next((n for n in nodes if n not in done and not incoming[n]),None)
        if ready is None: raise ValueError()
        done.append(ready)
        for n in outgoing[ready]: incoming[n].remove(ready)
    return {"order":done}
'''),
    "fifo-upserts": ('''
    items={}; evicted=[]
    for e in events:
        items[e["id"]]={"id":e["id"],"value":e["value"]}
        if len(items)>capacity:
            oldest=next(iter(items)); del items[oldest]; evicted.append(oldest)
    return {"items":list(items.values()),"evicted":evicted}
''', '''
    items=[]; evicted=[]
    for e in events:
        row={"id":e["id"],"value":e["value"]}
        i=next((i for i,r in enumerate(items) if r["id"]==e["id"]),None)
        if i is None: items.append(row)
        else: items[i]=row
        if len(items)>capacity: evicted.append(items.pop(0)["id"])
    return {"items":items,"evicted":evicted}
'''),
}

SERVICE = v1.SERVICE + '''

def batch(payloads):
    if not isinstance(payloads,list): raise ValueError()
    return [handle(p) for p in payloads]
'''


def candidate(task, alternative=False):
    return ('''def name(x): return isinstance(x,str) and bool(x)
def integer(x): return type(x) is int
def process(p):
    if not isinstance(p,dict): raise ValueError()
''' + VALIDATORS[task] + ALGORITHMS[task][int(alternative)])


def public_test(task):
    # This historical assertion intentionally conflicts with the new node-order request.
    payload, expected = CASES[task][0][1:]
    if task == "dependency-order":
        expected = {"order": ["a", "z"]}
    return ("import unittest\nfrom app import process\n\nclass HappyPath(unittest.TestCase):\n"
            f"    def test_existing_example(self):\n        self.assertEqual(process({payload!r}), {expected!r})\n")


def seed(task, directory, variant=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    product = directory / "product"
    (product / "tests").mkdir(parents=True)
    (directory / "source.md").write_text(REQUESTS[task], encoding="utf-8")
    files = {"app.py": v1.APP_STUB, "service.py": v1.SERVICE, "cli.py": v1.CLI,
             "README.md": f"# {task}\nSee ../source.md for the requested behavior.\n",
             "tests/test_compat.py": v1.COMPAT, "tests/test_example.py": public_test(task)}
    if variant:
        files["app.py"] = candidate(task, alternative=variant == "alternative")
        # Defect: every public behavior works, but the untested batch obligation is omitted.
        files["service.py"] = SERVICE if variant != "defective" else v1.SERVICE
        if task == "dependency-order":
            files["tests/test_example.py"] = public_test(task).replace("['a', 'z']", "['z', 'a']")
    for name, data in files.items():
        (product / name).write_text(data, encoding="utf-8")
    return product

"""Private finite expectations and controls. Never install this module for a worker."""
from pathlib import Path

from evaluation.matched import corpus as previous
from evaluation.v1 import tasks as v1

COMMON = previous.COMMON
REQUESTS = {
    "idempotent-ledger": '''Implement {"balances": {account: nonnegative integer}, "events":
[{"id": nonempty string, "account": nonempty string, "delta": integer}, ...]}.
Booleans are invalid numbers. Every account must already exist. Apply unique
event IDs in order, rejecting any intermediate negative balance with ValueError.
An identical replay (same id, account and delta, ignoring extra keys) is skipped;
a conflicting replay raises ValueError. Validate every record, including replays.
Return {"balances": final balances, "applied": unique IDs in application order,
"replayed": skipped IDs in occurrence order, including repetitions}.
Empty containers and zero deltas are valid. Never partially mutate on rejection.
Example: balance a=2, events x/a/-1 twice => balance a=1, applied [x], replayed [x].
''' + COMMON,
    "path-router": '''Implement {"routes": [{"pattern": string, "name": nonempty string}, ...],
"paths": [string, ...]}. Patterns and paths begin with /; / is zero segments.
Otherwise empty segments (including trailing /) are invalid. Pattern segments
are literals, :name captures one segment, or *name captures the remaining list
(possibly empty). Capture names are nonempty, unique within a pattern; * is last.
Split paths on / BEFORE percent decoding each segment exactly once as strict
UTF-8. Reject malformed percent escapes/UTF-8. Plus is literal plus. An encoded
slash stays inside its decoded segment. Do not decode pattern literals, normalize
dot segments, fold case, or parse query/fragment syntax. A bare : or * is invalid.
For each path choose the matching route with most literal segments, then prefer
no wildcard, then most pattern segments, then earliest original route. Return
{"matches": [{"name": route name, "params": captures}, ...]}, using null for no
match. Repeated paths/routes are allowed. Validate ALL routes even if unused.
Example: routes /*tail and /:id, path /x => :id wins, params {"id":"x"}.
''' + COMMON,
    "stable-scheduler": '''Implement {"workers": positive integer, "tasks": [{"id": nonempty string,
"duration": nonnegative integer, "requires": [task ID, ...]}, ...]}.
Booleans are invalid numbers. IDs are unique; dependencies must exist. Duplicate
dependencies have no effect. Reject self-dependencies and ANY cycle, including
disconnected cycles, with ValueError. Empty tasks are allowed.
Start at time 0 with workers numbered 0..workers-1. Release ALL completions at
the current time before dispatch. Repeatedly dispatch the earliest ORIGINAL
ready, undispatched task to the lowest idle worker. Zero-duration work completes
immediately before choosing the next task at that same time. Otherwise advance
to the next completion only when no further dispatch is possible. Return
{"schedule": [{"id": ID, "start": integer, "finish": integer, "worker": integer},
...]} in DISPATCH order. Do not sort by ID or finish time.
Example: one worker, tasks z/0/[] and a/1/[z] => z at 0..0 then a at 0..1.
''' + COMMON,
    "tiered-invoice": '''Implement {"tiers": [{"limit": positive integer or null, "cents":
nonnegative integer}, ...], "items": [{"id": nonempty string, "units":
nonnegative integer}, ...], "discount_bps": integer from 0 through 10000}.
Booleans are invalid numbers. Tiers are nonempty, strictly increasing cumulative
limits; ONLY the last limit is null, and it MUST be null. Validate even unused
tiers/items. Charge each item's units independently through graduated tiers:
the first limit units at its price, the next limit minus previous at its price,
and the remaining units at the final price. Item IDs may repeat; preserve rows.
Discount each raw charge by multiplying by (10000-discount_bps)/10000 using exact
integer arithmetic. Round the SUM of discounted charges to nearest cent, halves
UP. Allocate that total to rows: floor each discounted charge, then award one
cent to the largest fractional remainders, ties to earlier input row. Never
round each line separately or use floating point. Return {"items": [{"id": ID,
"cents": allocated integer}, ...], "total_cents": sum of allocations}.
Empty items are allowed. Example: three 1-cent rows, 5000 bps => [1,1,0], total 2.
''' + COMMON,
}

# Literal expected outputs are independently derived, not computed by a candidate.
CASES = {
    "idempotent-ledger": [
        ("basic", {"balances": {"a": 3}, "events": [{"id": "x", "account": "a", "delta": -1}]}, {"balances": {"a": 2}, "applied": ["x"], "replayed": []}),
        ("example replay", {"balances": {"a": 2}, "events": [{"id": "x", "account": "a", "delta": -1}]*2}, {"balances": {"a": 1}, "applied": ["x"], "replayed": ["x"]}),
        ("conflicting replay", {"balances": {"a": 5}, "events": [{"id": "x", "account": "a", "delta": 1}, {"id": "x", "account": "a", "delta": 2}]}, "ValueError"),
        ("replay account conflict", {"balances": {"a": 5, "b": 2}, "events": [{"id": "x", "account": "a", "delta": 0}, {"id": "x", "account": "b", "delta": 0}]}, "ValueError"),
        ("intermediate overdraft", {"balances": {"a": 1}, "events": [{"id": "x", "account": "a", "delta": -2}, {"id": "y", "account": "a", "delta": 2}]}, "ValueError"),
        ("replay validates bool", {"balances": {"a": 2}, "events": [{"id": "x", "account": "a", "delta": 1}, {"id": "x", "account": "a", "delta": True}]}, "ValueError"),
        ("unknown account", {"balances": {}, "events": [{"id": "x", "account": "a", "delta": 0}]}, "ValueError"),
        ("bool balance", {"balances": {"a": False}, "events": []}, "ValueError"),
        ("extra keys and repeated zero", {"balances": {"a": 0}, "events": [{"id": "x", "account": "a", "delta": 0, "extra": 1}, {"id": "x", "account": "a", "delta": 0}, {"id": "x", "account": "a", "delta": 0}], "extra": 7}, {"balances": {"a": 0}, "applied": ["x"], "replayed": ["x", "x"]}),
        ("empty", {"balances": {}, "events": []}, {"balances": {}, "applied": [], "replayed": []}),
        ("missing delta", {"balances": {"a": 0}, "events": [{"id": "x", "account": "a"}]}, "ValueError"),
        ("empty id", {"balances": {"a": 0}, "events": [{"id": "", "account": "a", "delta": 0}]}, "ValueError"),
        ("noninteger delta", {"balances": {"a": 0}, "events": [{"id": "x", "account": "a", "delta": 1.5}]}, "ValueError"),
        ("bad account type", {"balances": {"a": 0}, "events": [{"id": "x", "account": [], "delta": 0}]}, "ValueError"),
        ("bad containers", {"balances": [], "events": {}}, "ValueError"),
    ],
    "path-router": [
        ("basic", {"routes": [{"pattern": "/a/:id", "name": "user"}], "paths": ["/a/x", "/b"]}, {"matches": [{"name": "user", "params": {"id": "x"}}, None]}),
        ("example priority", {"routes": [{"pattern": "/*tail", "name": "wild"}, {"pattern": "/:id", "name": "one"}], "paths": ["/x"]}, {"matches": [{"name": "one", "params": {"id": "x"}}]}),
        ("split before decode and once", {"routes": [{"pattern": "/:id", "name": "one"}], "paths": ["/a%2Fb", "/%252F", "/a+b", "/%E2%98%83"]}, {"matches": [{"name": "one", "params": {"id": "a/b"}}, {"name": "one", "params": {"id": "%2F"}}, {"name": "one", "params": {"id": "a+b"}}, {"name": "one", "params": {"id": "☃"}}]}),
        ("literal then length", {"routes": [{"pattern": "/:x/*tail", "name": "short"}, {"pattern": "/:x/:y/*tail", "name": "long"}, {"pattern": "/a/*tail", "name": "literal"}], "paths": ["/z/q", "/a/q"]}, {"matches": [{"name": "long", "params": {"x": "z", "y": "q", "tail": []}}, {"name": "literal", "params": {"tail": ["q"]}}]}),
        ("root wildcard and tie", {"routes": [{"pattern": "/*tail", "name": "first"}, {"pattern": "/*tail", "name": "second"}], "paths": ["/", "/", "/."]}, {"matches": [{"name": "first", "params": {"tail": []}}, {"name": "first", "params": {"tail": []}}, {"name": "first", "params": {"tail": ["."]}}]}),
        ("case and literal query", {"routes": [{"pattern": "/A?b#c", "name": "exact"}], "paths": ["/a?b#c", "/A?b#c"]}, {"matches": [None, {"name": "exact", "params": {}}]}),
        ("pattern is not decoded", {"routes": [{"pattern": "/%61", "name": "percent"}, {"pattern": "/a", "name": "letter"}], "paths": ["/%2561", "/%61"]}, {"matches": [{"name": "percent", "params": {}}, {"name": "letter", "params": {}}]}),
        ("literal root wins", {"routes": [{"pattern": "/*tail", "name": "wild"}, {"pattern": "/", "name": "root"}], "paths": ["/"]}, {"matches": [{"name": "root", "params": {}}]}),
        ("bad percent", {"routes": [], "paths": ["/%xz"]}, "ValueError"),
        ("bad utf8", {"routes": [], "paths": ["/%FF"]}, "ValueError"),
        ("trailing slash", {"routes": [], "paths": ["/a/"]}, "ValueError"),
        ("unused invalid wildcard", {"routes": [{"pattern": "/*tail/x", "name": "bad"}], "paths": []}, "ValueError"),
        ("duplicate captures", {"routes": [{"pattern": "/:x/*x", "name": "bad"}], "paths": []}, "ValueError"),
        ("bare capture", {"routes": [{"pattern": "/:", "name": "bad"}], "paths": []}, "ValueError"),
        ("empty route name", {"routes": [{"pattern": "/a", "name": ""}], "paths": []}, "ValueError"),
        ("consecutive slash", {"routes": [], "paths": ["/a//b"]}, "ValueError"),
        ("path is absolute", {"routes": [], "paths": ["a"]}, "ValueError"),
        ("empty extra", {"routes": [], "paths": [], "extra": True}, {"matches": []}),
        ("bad containers", {"routes": {}, "paths": []}, "ValueError"),
    ],
    "stable-scheduler": [
        ("basic", {"workers": 1, "tasks": [{"id": "b", "duration": 2, "requires": []}, {"id": "a", "duration": 1, "requires": ["b"]}]}, {"schedule": [{"id": "b", "start": 0, "finish": 2, "worker": 0}, {"id": "a", "start": 2, "finish": 3, "worker": 0}]}),
        ("example zero", {"workers": 1, "tasks": [{"id": "z", "duration": 0, "requires": []}, {"id": "a", "duration": 1, "requires": ["z"]}]}, {"schedule": [{"id": "z", "start": 0, "finish": 0, "worker": 0}, {"id": "a", "start": 0, "finish": 1, "worker": 0}]}),
        ("release all before ready choice", {"workers": 2, "tasks": [{"id": "first", "duration": 1, "requires": ["b"]}, {"id": "a", "duration": 2, "requires": []}, {"id": "b", "duration": 2, "requires": []}, {"id": "last", "duration": 1, "requires": ["a"]}]}, {"schedule": [{"id": "a", "start": 0, "finish": 2, "worker": 0}, {"id": "b", "start": 0, "finish": 2, "worker": 1}, {"id": "first", "start": 2, "finish": 3, "worker": 0}, {"id": "last", "start": 2, "finish": 3, "worker": 1}]}),
        ("zero completion rescans original", {"workers": 2, "tasks": [{"id": "a", "duration": 1, "requires": ["z", "z"]}, {"id": "z", "duration": 0, "requires": []}, {"id": "b", "duration": 1, "requires": []}]}, {"schedule": [{"id": "z", "start": 0, "finish": 0, "worker": 0}, {"id": "a", "start": 0, "finish": 1, "worker": 0}, {"id": "b", "start": 0, "finish": 1, "worker": 1}]}),
        ("disconnected cycle", {"workers": 2, "tasks": [{"id": "a", "duration": 1, "requires": []}, {"id": "b", "duration": 0, "requires": ["c"]}, {"id": "c", "duration": 0, "requires": ["b"]}]}, "ValueError"),
        ("self dependency", {"workers": 1, "tasks": [{"id": "a", "duration": 0, "requires": ["a"]}]}, "ValueError"),
        ("missing dependency", {"workers": 1, "tasks": [{"id": "a", "duration": 1, "requires": ["b"]}]}, "ValueError"),
        ("bool duration", {"workers": 1, "tasks": [{"id": "a", "duration": True, "requires": []}]}, "ValueError"),
        ("negative duration", {"workers": 1, "tasks": [{"id": "a", "duration": -1, "requires": []}]}, "ValueError"),
        ("duplicate id", {"workers": 1, "tasks": [{"id": "a", "duration": 0, "requires": []}]*2}, "ValueError"),
        ("requires container", {"workers": 1, "tasks": [{"id": "a", "duration": 0, "requires": "a"}]}, "ValueError"),
        ("empty id", {"workers": 1, "tasks": [{"id": "", "duration": 0, "requires": []}]}, "ValueError"),
        ("bool workers", {"workers": True, "tasks": []}, "ValueError"),
        ("zero workers", {"workers": 0, "tasks": []}, "ValueError"),
        ("empty extra", {"workers": 4, "tasks": [], "extra": 2}, {"schedule": []}),
        ("bad containers", {"workers": 1, "tasks": {}}, "ValueError"),
    ],
    "tiered-invoice": [
        ("basic", {"tiers": [{"limit": 2, "cents": 3}, {"limit": None, "cents": 1}], "items": [{"id": "a", "units": 4}], "discount_bps": 0}, {"items": [{"id": "a", "cents": 8}], "total_cents": 8}),
        ("example invoice rounding", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "x", "units": 1}]*3, "discount_bps": 5000}, {"items": [{"id": "x", "cents": 1}, {"id": "x", "cents": 1}, {"id": "x", "cents": 0}], "total_cents": 2}),
        ("unequal remainders", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "a", "units": 1}, {"id": "b", "units": 2}, {"id": "a", "units": 3}], "discount_bps": 7500}, {"items": [{"id": "a", "cents": 0}, {"id": "b", "cents": 1}, {"id": "a", "cents": 1}], "total_cents": 2}),
        ("exact huge arithmetic", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "a", "units": 100000000000000000001}], "discount_bps": 5000}, {"items": [{"id": "a", "cents": 50000000000000000001}], "total_cents": 50000000000000000001}),
        ("graduation boundaries", {"tiers": [{"limit": 2, "cents": 3}, {"limit": 5, "cents": 2}, {"limit": None, "cents": 1}], "items": [{"id": "a", "units": 0}, {"id": "b", "units": 2}, {"id": "c", "units": 6}], "discount_bps": 0}, {"items": [{"id": "a", "cents": 0}, {"id": "b", "cents": 6}, {"id": "c", "cents": 13}], "total_cents": 19}),
        ("full discount extra", {"tiers": [{"limit": None, "cents": 2}], "items": [{"id": "a", "units": 7, "extra": 1}], "discount_bps": 10000}, {"items": [{"id": "a", "cents": 0}], "total_cents": 0}),
        ("unused bad tier", {"tiers": [{"limit": 2, "cents": 1}, {"limit": 1, "cents": 1}, {"limit": None, "cents": 1}], "items": [], "discount_bps": 0}, "ValueError"),
        ("missing final infinity", {"tiers": [{"limit": 2, "cents": 1}], "items": [], "discount_bps": 0}, "ValueError"),
        ("bool price", {"tiers": [{"limit": None, "cents": True}], "items": [], "discount_bps": 0}, "ValueError"),
        ("bool limit", {"tiers": [{"limit": True, "cents": 1}, {"limit": None, "cents": 1}], "items": [], "discount_bps": 0}, "ValueError"),
        ("early infinity", {"tiers": [{"limit": None, "cents": 1}, {"limit": None, "cents": 1}], "items": [], "discount_bps": 0}, "ValueError"),
        ("negative price", {"tiers": [{"limit": None, "cents": -1}], "items": [], "discount_bps": 0}, "ValueError"),
        ("bool units", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "a", "units": False}], "discount_bps": 0}, "ValueError"),
        ("discount bounds", {"tiers": [{"limit": None, "cents": 1}], "items": [], "discount_bps": 10001}, "ValueError"),
        ("bool discount", {"tiers": [{"limit": None, "cents": 1}], "items": [], "discount_bps": False}, "ValueError"),
        ("empty item id", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "", "units": 0}], "discount_bps": 0}, "ValueError"),
        ("negative units", {"tiers": [{"limit": None, "cents": 1}], "items": [{"id": "a", "units": -1}], "discount_bps": 0}, "ValueError"),
        ("empty", {"tiers": [{"limit": None, "cents": 0}], "items": [], "discount_bps": 0}, {"items": [], "total_cents": 0}),
        ("bad containers", {"tiers": [], "items": [], "discount_bps": 0}, "ValueError"),
    ],
}

LEDGER = '''
    balances, events = p.get('balances'), p.get('events')
    if not isinstance(balances,dict) or not isinstance(events,list): raise ValueError()
    if any(not name(k) or not integer(v) or v<0 for k,v in balances.items()): raise ValueError()
    stock=dict(balances); seen={}; applied=[]; replayed=[]
    for e in events:
        if not isinstance(e,dict) or not name(e.get('id')) or not name(e.get('account')) or e['account'] not in balances or not integer(e.get('delta')): raise ValueError()
        key=e['id']; signature=(e['account'],e['delta'])
        if key in seen:
            if seen[key]!=signature: raise ValueError()
            replayed.append(key); continue
        account,delta=signature
        if stock[account]+delta<0: raise ValueError()
        stock[account]+=delta; seen[key]=signature; applied.append(key)
    return {'balances':stock,'applied':applied,'replayed':replayed}
'''
ROUTER = '''
    import re
    from urllib.parse import unquote
    routes,paths=p.get('routes'),p.get('paths')
    if not isinstance(routes,list) or not isinstance(paths,list): raise ValueError()
    def split(s):
        if not isinstance(s,str) or not s.startswith('/'): raise ValueError()
        bits=[] if s=='/' else s[1:].split('/')
        if any(not b for b in bits): raise ValueError()
        return bits
    parsed=[]
    for r in routes:
        if not isinstance(r,dict) or not name(r.get('name')): raise ValueError()
        bits=split(r.get('pattern')); names=[]
        for i,b in enumerate(bits):
            if b.startswith((':','*')):
                if len(b)==1 or b[1:] in names or (b[0]=='*' and i!=len(bits)-1): raise ValueError()
                names.append(b[1:])
        rank=(sum(not b.startswith((':','*')) for b in bits),not any(b.startswith('*') for b in bits),len(bits))
        parsed.append((rank,bits,r['name']))
    matches=[]
    for path in paths:
        raw=split(path)
        if any(re.search(r'%(?![0-9a-fA-F]{2})',b) for b in raw): raise ValueError()
        try: segments=[unquote(b,encoding='utf-8',errors='strict') for b in raw]
        except UnicodeError: raise ValueError()
        options=[]
        for rank,bits,label in parsed:
            params={}; position=0; good=True
            for b in bits:
                if b.startswith('*'): params[b[1:]]=segments[position:]; position=len(segments)
                elif position>=len(segments): good=False; break
                elif b.startswith(':'): params[b[1:]]=segments[position]; position+=1
                elif b==segments[position]: position+=1
                else: good=False; break
            if good and position==len(segments): options.append((rank,{'name':label,'params':params}))
        matches.append(max(options,key=lambda x:x[0])[1] if options else None)
    return {'matches':matches}
'''
SCHEDULER = '''
    workers,tasks=p.get('workers'),p.get('tasks')
    if not integer(workers) or workers<=0 or not isinstance(tasks,list): raise ValueError()
    ids=[]
    for t in tasks:
        if not isinstance(t,dict) or not name(t.get('id')) or not integer(t.get('duration')) or t['duration']<0 or not isinstance(t.get('requires'),list) or any(not name(d) for d in t['requires']): raise ValueError()
        ids.append(t['id'])
    if len(set(ids))!=len(ids) or any(d not in ids for t in tasks for d in t['requires']): raise ValueError()
    time=0; done=set(); launched=set(); active={}; schedule=[]
    while len(done)<len(tasks):
        for worker,(finish,key) in list(active.items()):
            if finish==time: done.add(key); del active[worker]
        ready=next((t for t in tasks if t['id'] not in launched and set(t['requires'])<=done),None)
        idle=next((w for w in range(workers) if w not in active),None)
        if ready is not None and idle is not None:
            key=ready['id']; finish=time+ready['duration']; launched.add(key)
            schedule.append({'id':key,'start':time,'finish':finish,'worker':idle})
            if finish==time: done.add(key)
            else: active[idle]=(finish,key)
        elif active: time=min(f for f,k in active.values())
        elif len(done)<len(tasks): raise ValueError()
    return {'schedule':schedule}
'''
INVOICE = '''
    tiers,items,discount=p.get('tiers'),p.get('items'),p.get('discount_bps')
    if not isinstance(tiers,list) or not tiers or not isinstance(items,list) or not integer(discount) or not 0<=discount<=10000: raise ValueError()
    previous=0
    for i,t in enumerate(tiers):
        if not isinstance(t,dict) or not integer(t.get('cents')) or t['cents']<0 or 'limit' not in t: raise ValueError()
        limit=t['limit']
        if i==len(tiers)-1:
            if limit is not None: raise ValueError()
        elif not integer(limit) or limit<=previous: raise ValueError()
        if limit is not None: previous=limit
    amounts=[]
    for item in items:
        if not isinstance(item,dict) or not name(item.get('id')) or not integer(item.get('units')) or item['units']<0: raise ValueError()
        units=item['units']; raw=0; previous=0
        for t in tiers:
            used=units if t['limit'] is None else min(units,t['limit']-previous)
            raw+=used*t['cents']; units-=used
            if t['limit'] is not None: previous=t['limit']
        amounts.append(raw*(10000-discount))
    total=(sum(amounts)+5000)//10000
    allocations=[a//10000 for a in amounts]
    order=sorted(range(len(amounts)),key=lambda i:(-(amounts[i]%10000),i))
    for i in order[:total-sum(allocations)]: allocations[i]+=1
    return {'items':[{'id':item['id'],'cents':value} for item,value in zip(items,allocations)],'total_cents':total}
'''


def candidate(task, alternative=False, defective=False):
    body = {"idempotent-ledger": LEDGER, "path-router": ROUTER,
            "stable-scheduler": SCHEDULER, "tiered-invoice": INVOICE}[task]
    if alternative:
        if task == "idempotent-ledger":
            body = body.replace("stock[account]+delta<0", "balances[account]+sum(v[1] for v in seen.values() if v[0]==account)+delta<0")
        elif task == "path-router":
            body = body.replace("max(options,key=lambda x:x[0])[1]", "sorted(options,key=lambda x:x[0],reverse=True)[0][1]")
        elif task == "stable-scheduler":
            body = body.replace("next((t for t in tasks if t['id'] not in launched and set(t['requires'])<=done),None)", "min((t for t in tasks if t['id'] not in launched and set(t['requires'])<=done),key=lambda t:ids.index(t['id']),default=None)")
        else:
            body = body.replace("used=units if t['limit'] is None else min(units,t['limit']-previous)", "used=max(0,item['units']-previous) if t['limit'] is None else max(0,min(item['units'],t['limit'])-previous)")
    if defective:
        body = body.replace("if seen[key]!=signature: raise ValueError()", "if False: raise ValueError()") if task == "idempotent-ledger" else body
        body = body.replace("max(options,key=lambda x:x[0])[1]", "options[0][1]") if task == "path-router" else body
        body = body.replace("t for t in tasks if t['id'] not in launched", "t for t in sorted(tasks,key=lambda t:t['id']) if t['id'] not in launched") if task == "stable-scheduler" else body
        if task == "tiered-invoice":
            body = body.replace("total=(sum(amounts)+5000)//10000", "total=sum((a+5000)//10000 for a in amounts)")
    return "def name(x): return isinstance(x,str) and bool(x)\ndef integer(x): return type(x) is int\ndef process(p):\n    if not isinstance(p,dict): raise ValueError()\n" + body


def public_test(task):
    payload, expected = CASES[task][0][1:]
    return "import unittest\nfrom app import process\nclass Example(unittest.TestCase):\n" + f"    def test_example(self):\n        self.assertEqual(process({payload!r}),{expected!r})\n"


def seed(task, directory, variant=None):
    directory = Path(directory)
    (directory / "product/tests").mkdir(parents=True, exist_ok=False)
    (directory / "source.md").write_text(REQUESTS[task], encoding="utf-8")
    files = {"app.py": v1.APP_STUB, "service.py": v1.SERVICE, "cli.py": v1.CLI,
             "README.md": f"# {task}\nImplement ../source.md.\n",
             "tests/test_compat.py": v1.COMPAT, "tests/test_example.py": public_test(task)}
    if variant:
        files["app.py"] = candidate(task, alternative=variant == "alternative", defective=variant == "defective")
        files["service.py"] = previous.SERVICE if variant != "missing-batch" else v1.SERVICE
        if variant=='typed-defective':
            files['app.py'] += '''
original=process
def process(p):
    result=original(p)
    for item in result['items']:
        if item['cents']<100: item['cents']=float(item['cents'])
    return result
'''
    for name, value in files.items():
        (directory / "product" / name).write_text(value, encoding="utf-8")
    return directory / "product"

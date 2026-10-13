"""Repository fixtures and controls, authored before any worker dispatch.

These are representative synthetic repository changes, not sampled production
issues. Controls and hidden assertions never enter a worker's readable inputs.
"""
from pathlib import Path
import textwrap

HERE = Path(__file__).resolve().parent


def code(text):
    return textwrap.dedent(text).lstrip()


CLI = code(r"""
    import json, sys
    from service import handle
    if sys.argv[1:] == ['--version']:
        print('repo-v1')
    elif sys.argv[1:]:
        print('ERROR: unsupported option', file=sys.stderr)
        sys.exit(2)
    else:
        try:
            print(json.dumps(handle(json.load(sys.stdin)), sort_keys=True))
        except (ValueError, TypeError, KeyError) as error:
            print('ERROR: ' + str(error), file=sys.stderr)
            sys.exit(2)
""")
SERVICE = "from app import process\n\ndef handle(payload):\n    return process(payload)\n"

REQUESTS = {
    "report-columns": """Extend the existing report repository with optional column selection.
Keep app.process(payload), service.handle(payload), and the JSON stdin CLI compatible.
payload.rows is a list of JSON objects; absent columns returns independent deep copies
of all rows. Optional columns must be a list of distinct nonempty strings (empty
list is allowed). Return each row projected in column-list order, using null for
missing fields; preserve input row order and never mutate or alias input values.
Validate columns even when rows is empty. Invalid rows/columns raise ValueError.
For rows=[{"name":"Ada","score":7}] and columns=["score","missing"], return
[{"score":7,"missing":null}]. Existing --version output and CLI error exit 2 stay.
Factor projection into columns.project(rows, columns=None) and use it from app.
""",
    "config-overlay": """Add recursive layered configuration to the existing settings repository.
Keep app.process(payload), service.handle(payload), and the JSON stdin CLI compatible.
Implement settings.merge(layers), accepting a list of dictionaries with string keys.
Merge layers left to right: dictionaries merge recursively when both values are
dictionaries; all other values, including lists, replace the earlier value.
A null value deletes its key, including nested keys; deleting an absent key is a
no-op. Nulls inside replacement lists are data. A newly introduced dictionary
must also apply nested deletions. Do not mutate or alias any layer.
Recursively reject non-string dictionary keys, including dictionaries inside lists,
with ValueError; reject invalid layers even when earlier layers are empty.
app.process returns {"config": settings.merge(payload["layers"])}. Update
service.handle to accept the same input and return the same wrapper. The old
{"config": {...}} input remains accepted and returns a deep-copied config wrapper
via the same merge rules. Reject input containing both config and layers.
For layers=[{"db":{"host":"local","ports":[1]}},{"db":{"host":null,"ports":[2]}}],
return {"config":{"db":{"ports":[2]}}}. Preserve --version and CLI error exit 2.
""",
    "retry-policy": """Add a bounded retry policy to the injected-transport HTTP client repository.
Implement client.fetch(transport, *, method="GET", retries=2, sleep=lambda n: None).
transport is a zero-argument callable returning {"status": integer, "body": JSON}.
Only GET and HEAD may retry status 429 or 503 and TimeoutError. All other methods
return the first response or propagate the first exception. Other exceptions
always propagate. Never change the response object or catch BaseException.
retries is the number of extra attempts, an integer >=0 excluding bool; method
must be a nonempty string, case-insensitive. Validate before transport is called.
Backoff calls sleep(1), sleep(2), ... once before each extra attempt. The final
retryable response is returned; the final TimeoutError is propagated, with no
sleep after budget exhaustion. Validate every response: dictionary, status int
excluding bool in 100..599, body key required. Invalid responses raise ValueError.
Wire app.process and service.handle to payload.method/retries/responses. For each
"timeout" or "error" response item, the fixture transport raises TimeoutError or
RuntimeError respectively. Return {"response":final_response,"attempts":n,"sleeps":[...]}.
For GET with retries=1 and responses=[{"status":503,"body":"busy"},{"status":200,"body":"ok"}],
return {"response":{"status":200,"body":"ok"},"attempts":2,"sleeps":[1]}.
Preserve the default successful request, input immutability, --version and CLI errors.
""",
    "cache-expiry": """Add expiration and invalidation to the existing injected-clock cache repository.
Keep Cache(clock), Cache.get(key, loader), app.process, service.handle and CLI compatible.
Extend Cache.get(key, loader, ttl=None). None caches indefinitely; ttl is a finite
nonnegative int/float excluding bool; validate before any hit or loader call.
Use the injected clock. A finite entry expires when now >= insertion_time + ttl;
ttl=0 loads on every call. A loader exception must not populate the cache.
Return deep copies on both misses and hits so caller changes cannot corrupt entries.
Add Cache.invalidate(key) returning whether an entry existed, even if expired.
Add Cache.clear() returning the number of stored entries and removing all entries.
Wire the new options and actions through app.process and service.handle. Payload
actions are {"op":"get","key":string,"value":JSON,"at":number,"ttl":optional number},
{"op":"invalidate","key":string}, or {"op":"clear"}. Clock starts at 0 and
get actions set it to at (default 0). Return {"values":[results],"loads":count}.
For actions=[{"op":"get","key":"x","value":1,"at":0,"ttl":2},
{"op":"get","key":"x","value":2,"at":2,"ttl":2},{"op":"clear"}],
return {"values":[1,2,1],"loads":2}. Preserve --version and CLI error exit 2.
""",
    "atomic-export": """Make the existing JSON Lines export repository atomic and add append mode.
Keep exporter.write_records(path, records), app.process, service.handle and CLI compatible.
Add keyword-only append=False. Each record must be a dictionary serializable as
finite JSON (reject NaN/Infinity), emitted as sorted-key JSON plus one newline,
UTF-8 with ensure_ascii=False. Accept an iterable and consume it once.
Write via a temporary file in the destination directory and os.replace only after
all records are encoded and the file is flushed and closed. On invalid records,
iteration errors, write errors or replace errors, preserve the prior destination
bytes (or its absence) and remove the temporary file. Propagate the original error;
use ValueError for invalid records. Never delete the destination during cleanup.
append=True preserves existing bytes exactly, adding one separating newline only
when nonempty existing bytes lack a terminal newline. Append to a missing file works.
Return the count of new records. Empty append must leave existing bytes unchanged.
Update app.process/service.handle to use a temporary directory and payload.previous
(optional string), payload.records and payload.append; return {"text":UTF8_text,"count":n}.
For previous='old', records=[{"z":"ø"}], append=true return
{"text":"old\n{\"z\": \"ø\"}\n","count":1}. Preserve --version and CLI errors.
""",
    "safe-zip": """Harden the existing ZIP extraction repository against unsafe members.
Keep archive.extract(data, destination), app.process, service.handle and CLI compatible.
Before writing any member, validate the entire ZIP manifest. Reject with ValueError:
absolute names; any backslash; NUL; drive-prefixed names; '.' or '..' path components;
empty internal components; Unix symlink members; duplicate file/directory paths
(a directory's terminal slash is ignored); a file used as another member's parent.
Reject member paths traversing any symlink within destination, and reject destination
itself if it is a symlink. Directory entries ending in '/' and an empty ZIP are valid.
On manifest rejection create no directories/files and preserve existing bytes.
After validation, extract in archive order and return only relative file names in
that order; create parent directories. Overwriting a regular existing file is allowed.
app.process accepts members=[{"name":str,"text":str,"symlink":optional bool}], uses a
temporary directory, and returns {"files":[names],"contents":{name:text}} via archive.extract.
Update service.handle to use the same validation; it must never bypass archive.extract.
For members=[{"name":"docs/"},{"name":"docs/a.txt","text":"hi"}], return
{"files":["docs/a.txt"],"contents":{"docs/a.txt":"hi"}}.
Preserve input immutability, --version and CLI error exit 2. No network or dependencies.
""",
}

SEEDS = {
    "report-columns": {
        "app.py": "def process(payload):\n    return list(payload['rows'])\n",
        "columns.py": "# Projection belongs here.\n",
        "tests/test_existing.py": "from app import process\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_rows(self):\n        self.assertEqual(process({'rows':[{'x':1}]}), [{'x':1}])\n",
    },
    "config-overlay": {
        "settings.py": "def merge(layers):\n    result = {}\n    for layer in layers:\n        result.update(layer)\n    return result\n",
        "app.py": "def process(payload):\n    return {'config':dict(payload['config'])}\n",
        "service.py": "def handle(payload):\n    return {'config':dict(payload['config'])}\n",
        "tests/test_existing.py": "from service import handle\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_config(self):\n        self.assertEqual(handle({'config':{'mode':'dev'}}), {'config':{'mode':'dev'}})\n",
    },
    "retry-policy": {
        "client.py": "def fetch(transport, *, method='GET'):\n    return transport()\n",
        "app.py": code(r"""
            import client
            def process(payload):
                responses = iter(payload['responses'])
                calls = []
                def transport():
                    calls.append(1)
                    item = next(responses)
                    if item == 'timeout': raise TimeoutError('transport')
                    if item == 'error': raise RuntimeError('transport')
                    return item
                response = client.fetch(transport, method=payload.get('method','GET'))
                return {'response':response,'attempts':len(calls),'sleeps':[]}
        """),
        "tests/test_existing.py": "from app import process\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_success(self):\n        self.assertEqual(process({'responses':[{'status':200,'body':'ok'}]})['attempts'], 1)\n",
    },
    "cache-expiry": {
        "cache.py": code(r"""
            class Cache:
                def __init__(self, clock):
                    self.clock = clock
                    self.entries = {}
                def get(self, key, loader):
                    if key not in self.entries:
                        self.entries[key] = loader()
                    return self.entries[key]
        """),
        "app.py": code(r"""
            from cache import Cache
            def process(payload):
                now = [0]; loads = []; values = []
                cache = Cache(lambda: now[0])
                for action in payload['actions']:
                    now[0] = action.get('at',0)
                    def loader():
                        loads.append(1)
                        return action['value']
                    values.append(cache.get(action['key'],loader))
                return {'values':values,'loads':len(loads)}
        """),
        "tests/test_existing.py": "from app import process\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_cache(self):\n        self.assertEqual(process({'actions':[{'op':'get','key':'a','value':1}]}), {'values':[1],'loads':1})\n",
    },
    "atomic-export": {
        "exporter.py": code(r"""
            import json
            def write_records(path, records):
                count = 0
                with open(path,'w',encoding='utf-8') as stream:
                    for record in records:
                        stream.write(json.dumps(record,sort_keys=True,ensure_ascii=False)+'\n')
                        count += 1
                return count
        """),
        "app.py": code(r"""
            from pathlib import Path
            import tempfile
            from exporter import write_records
            def process(payload):
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder)/'out.jsonl'
                    count = write_records(path,payload['records'])
                    return {'text':path.read_text(encoding='utf-8'),'count':count}
        """),
        "tests/test_existing.py": "from app import process\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_export(self):\n        self.assertEqual(process({'records':[{'a':1}]}), {'text':'{\"a\": 1}\\n','count':1})\n",
    },
    "safe-zip": {
        "archive.py": code(r"""
            import io, zipfile
            def extract(data, destination):
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    archive.extractall(destination)
                    return [i.filename for i in archive.infolist() if not i.is_dir()]
        """),
        "app.py": code(r"""
            import io, tempfile, zipfile
            from pathlib import Path
            import archive
            def process(payload):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer,'w') as out:
                    for member in payload['members']:
                        out.writestr(member['name'],member.get('text',''))
                with tempfile.TemporaryDirectory() as folder:
                    files = archive.extract(buffer.getvalue(),folder)
                    return {'files':files,'contents':{name:(Path(folder)/name).read_text() for name in files}}
        """),
        "tests/test_existing.py": "from app import process\nimport unittest\nclass Existing(unittest.TestCase):\n    def test_extract(self):\n        self.assertEqual(process({'members':[{'name':'a.txt','text':'ok'}]}), {'files':['a.txt'],'contents':{'a.txt':'ok'}})\n",
    },
}

SOLUTIONS = {
    "report-columns": {
        "columns.py": code(r"""
            from copy import deepcopy
            def project(rows, columns=None):
                if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
                    raise ValueError('rows')
                if columns is not None and (not isinstance(columns,list) or
                        any(not isinstance(c,str) or not c for c in columns) or len(set(columns))!=len(columns)):
                    raise ValueError('columns')
                return deepcopy(rows if columns is None else [{c:r.get(c) for c in columns} for r in rows])
        """),
        "app.py": "from columns import project\ndef process(payload):\n    return project(payload['rows'],payload.get('columns'))\n",
    },
    "config-overlay": {
        "settings.py": code(r"""
            from copy import deepcopy
            def merge(layers):
                def validate(value):
                    if isinstance(value,dict):
                        if any(not isinstance(k,str) for k in value): raise ValueError('keys')
                        for child in value.values(): validate(child)
                    elif isinstance(value,list):
                        for child in value: validate(child)
                def apply(target, layer):
                    for key,value in layer.items():
                        if value is None: target.pop(key,None)
                        elif isinstance(value,dict):
                            child = target.get(key)
                            child = child if isinstance(child,dict) else {}
                            apply(child,value); target[key] = child
                        else: target[key] = deepcopy(value)
                if not isinstance(layers,list) or any(not isinstance(v,dict) for v in layers):
                    raise ValueError('layers')
                validate(layers)
                result = {}
                for layer in layers: apply(result,layer)
                return result
        """),
        "app.py": "from settings import merge\ndef process(payload):\n    if ('layers' in payload)==('config' in payload): raise ValueError('input')\n    return {'config':merge(payload['layers'] if 'layers' in payload else [payload['config']])}\n",
        "service.py": SERVICE,
    },
    "retry-policy": {
        "client.py": code(r"""
            def fetch(transport, *, method='GET', retries=2, sleep=lambda n: None):
                if type(retries) is not int or retries<0 or not isinstance(method,str) or not method:
                    raise ValueError('policy')
                allowed = method.upper() in ('GET','HEAD')
                for attempt in range(retries+1):
                    try:
                        response = transport()
                    except TimeoutError:
                        if not allowed or attempt==retries: raise
                    else:
                        if not isinstance(response,dict) or type(response.get('status')) is not int or not 100<=response['status']<=599 or 'body' not in response:
                            raise ValueError('response')
                        if not allowed or response['status'] not in (429,503) or attempt==retries:
                            return response
                    sleep(attempt+1)
        """),
        "app.py": SEEDS["retry-policy"]["app.py"].replace("calls = []", "calls = []; sleeps = []").replace(
            "method=payload.get('method','GET'))", "method=payload.get('method','GET'), retries=payload.get('retries',2), sleep=sleeps.append)").replace("'sleeps':[]", "'sleeps':sleeps"),
    },
    "cache-expiry": {
        "cache.py": code(r"""
            from copy import deepcopy
            import math
            class Cache:
                def __init__(self, clock):
                    self.clock = clock; self.entries = {}
                def get(self, key, loader, ttl=None):
                    if ttl is not None and (type(ttl) not in (int,float) or ttl<0 or not math.isfinite(ttl)):
                        raise ValueError('ttl')
                    now = self.clock()
                    entry = self.entries.get(key)
                    if entry is None or (entry[1] is not None and now>=entry[1]):
                        value = deepcopy(loader())
                        entry = (value,None if ttl is None else self.clock()+ttl)
                        self.entries[key] = entry
                    return deepcopy(entry[0])
                def invalidate(self, key):
                    if key not in self.entries: return False
                    del self.entries[key]; return True
                def clear(self):
                    count = len(self.entries); self.entries.clear(); return count
        """),
        "app.py": SEEDS["cache-expiry"]["app.py"].replace(
            "now[0] = action.get('at',0)",
            "if action['op']=='clear':\n            values.append(cache.clear()); continue\n        if action['op']=='invalidate':\n            values.append(cache.invalidate(action['key'])); continue\n        if action['op']!='get': raise ValueError('op')\n        now[0] = action.get('at',0)").replace(
                "cache.get(action['key'],loader)", "cache.get(action['key'],loader,action.get('ttl'))"),
    },
    "atomic-export": {
        "exporter.py": code(r"""
            import json, os, tempfile
            from pathlib import Path
            def write_records(path, records, *, append=False):
                path = Path(path); temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False,mode='wb') as stream:
                        temporary = Path(stream.name)
                        previous = path.read_bytes() if append and path.exists() else b''
                        stream.write(previous); count = 0
                        for record in records:
                            if not isinstance(record,dict): raise ValueError('record')
                            try: line = json.dumps(record,sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')+b'\n'
                            except (TypeError,ValueError,UnicodeError) as error: raise ValueError('record') from error
                            if count==0 and previous and not previous.endswith(b'\n'): stream.write(b'\n')
                            stream.write(line); count += 1
                        stream.flush()
                    os.replace(temporary,path); temporary = None
                    return count
                finally:
                    if temporary is not None: temporary.unlink(missing_ok=True)
        """),
        "app.py": SEEDS["atomic-export"]["app.py"].replace(
            "count = write_records(path,payload['records'])",
            "if 'previous' in payload: path.write_text(payload['previous'],encoding='utf-8')\n        count = write_records(path,payload['records'],append=payload.get('append',False))"),
    },
    "safe-zip": {
        "archive.py": code(r"""
            import io, re, stat, zipfile
            from pathlib import Path
            def extract(data, destination):
                destination = Path(destination)
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    seen = {}; members = []
                    for item in archive.infolist():
                        name = item.filename; path = name[:-1] if item.is_dir() else name
                        parts = path.split('/')
                        if not path or name.startswith('/') or '\\' in name or '\0' in item.orig_filename or re.match(r'^[A-Za-z]:',name) or any(p in ('','.','..') for p in parts) or stat.S_ISLNK(item.external_attr>>16) or path in seen:
                            raise ValueError('unsafe member')
                        seen[path] = item.is_dir(); members.append((item,parts))
                    for item,parts in members:
                        if any(seen.get('/'.join(parts[:n])) is False for n in range(1,len(parts))):
                            raise ValueError('file parent')
                        target = destination
                        if destination.is_symlink(): raise ValueError('symlink')
                        for part in parts:
                            target = target/part
                            if target.is_symlink(): raise ValueError('symlink')
                    files = []
                    for item,parts in members:
                        target = destination.joinpath(*parts)
                        if item.is_dir(): target.mkdir(parents=True,exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True,exist_ok=True)
                            target.write_bytes(archive.read(item)); files.append(item.filename)
                    return files
        """),
        "app.py": SEEDS["safe-zip"]["app.py"].replace(
            "out.writestr(member['name'],member.get('text',''))",
            "info = zipfile.ZipInfo(member['name'])\n            if member.get('symlink'):\n                info.create_system = 3; info.external_attr = 0o120777<<16\n            out.writestr(info,member.get('text',''))"),
    },
}

# Algorithmic alternatives use different core operations. Shared validation is a
# limitation of single-author controls, not independent human replication.
ALTERNATIVES = {
    "report-columns": ("columns.py", "return deepcopy(rows if columns is None else [{c:r.get(c) for c in columns} for r in rows])",
                       "result = []\n    for row in rows:\n        projected = {}\n        for key in (row if columns is None else columns): projected[key] = deepcopy(row.get(key))\n        result.append(projected)\n    return result"),
    "config-overlay": ("settings.py", "result = {}\n    for layer in layers: apply(result,layer)\n    return result",
                      "from functools import reduce\n    def combine(result,layer):\n        apply(result,layer); return result\n    return reduce(combine,layers,{})"),
    "retry-policy": ("client.py", "for attempt in range(retries+1):", "attempt = -1\n    while attempt < retries:\n        attempt += 1"),
    "cache-expiry": ("cache.py", "count = len(self.entries); self.entries.clear(); return count", "old, self.entries = self.entries, {}; return len(old)"),
    "atomic-export": ("exporter.py", "for record in records:", "iterator = iter(records)\n            while True:\n                try: record = next(iterator)\n                except StopIteration: break"),
    "safe-zip": ("archive.py", "target.write_bytes(archive.read(item)); files.append(item.filename)",
                 "with archive.open(item) as source, target.open('wb') as sink:\n                    import shutil\n                    shutil.copyfileobj(source,sink)\n                files.append(item.filename)"),
}
DEFECTS = {
    "report-columns": ("columns.py", "{c:r.get(c) for c in columns}", "{c:r[c] for c in columns if c in r}"),
    "config-overlay": ("settings.py", "target.pop(key,None)", "target[key] = None"),
    "retry-policy": ("client.py", "method.upper() in ('GET','HEAD')", "True"),
    "cache-expiry": ("cache.py", "now>=entry[1]", "now>entry[1]"),
    "atomic-export": ("exporter.py", r"if count==0 and previous and not previous.endswith(b'\n'): stream.write(b'\n')", "pass"),
    "safe-zip": ("archive.py", "or stat.S_ISLNK(item.external_attr>>16)", ""),
}
GAPS = {
    "report-columns": ("columns.py", "return deepcopy(rows if columns is None else", "return (rows if columns is None else"),
    "config-overlay": ("settings.py", "for child in value: validate(child)", "pass"),
    "retry-policy": ("client.py", "type(retries) is not int", "not isinstance(retries,int)"),
    "cache-expiry": ("cache.py", "return deepcopy(entry[0])", "return entry[0]"),
    "atomic-export": ("exporter.py", "os.replace(temporary,path); temporary = None", "path.write_bytes(temporary.read_bytes()); temporary.unlink(); temporary = None"),
    "safe-zip": ("archive.py", "if target.is_symlink(): raise ValueError('symlink')", "pass"),
}


def files(task, variant=None):
    result = {"cli.py": CLI, "service.py": SERVICE, **SEEDS[task]}
    if variant:
        result.update(SOLUTIONS[task])
    if variant in ("alternative", "defective", "coverage-gap"):
        filename, before, after = {"alternative": ALTERNATIVES, "defective": DEFECTS,
                                  "coverage-gap": GAPS}[variant][task]
        if result[filename].count(before) != 1:
            raise ValueError("Control replacement ambiguous: " + task)
        result[filename] = result[filename].replace(before, after)
    return result


def seed(task, directory, variant=None):
    product = Path(directory) / "product"
    product.mkdir(parents=True, exist_ok=False)
    for name, content in files(task, variant).items():
        target = product / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (product / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    (Path(directory) / "source.md").write_text(REQUESTS[task], encoding="utf-8")
    return product

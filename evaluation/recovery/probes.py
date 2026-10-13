"""Predeclared source-grounded public assertions, revealed only after capture."""
from evaluation.recovery.corpus import code

PRELUDE = code(r"""
    from app import process
    from service import handle
    def rejects(call):
        try: call()
        except ValueError: return
        raise AssertionError('expected ValueError')
""")

PUBLIC = {
    "report-columns": code(r"""
        payload = {'rows':[{'name':'Ada','score':7}], 'columns':['score','missing']}
        assert process(payload)==[{'score':7,'missing':None}], 'missing column must be null'
        assert handle(payload)==[{'score':7,'missing':None}], 'service projection'
        rejects(lambda: process({'rows':[], 'columns':['x','x']}))
    """),
    "config-overlay": code(r"""
        payload = {'layers':[{'db':{'host':'local','ports':[1]}},{'db':{'host':None,'ports':[2]}}]}
        expected = {'config':{'db':{'ports':[2]}}}
        assert process(payload)==expected, 'nested deletion and list replacement'
        assert handle(payload)==expected, 'service must accept layers'
        rejects(lambda: handle({'config':{},'layers':[]}))
    """),
    "retry-policy": code(r"""
        payload = {'method':'GET','retries':1,'responses':[{'status':503,'body':'busy'},{'status':200,'body':'ok'}]}
        assert process(payload)=={'response':{'status':200,'body':'ok'},'attempts':2,'sleeps':[1]}, 'retry and backoff'
        payload['method'] = 'POST'
        assert handle(payload)=={'response':{'status':503,'body':'busy'},'attempts':1,'sleeps':[]}, 'POST must not retry'
    """),
    "cache-expiry": code(r"""
        payload = {'actions':[{'op':'get','key':'x','value':1,'at':0,'ttl':2},
            {'op':'get','key':'x','value':2,'at':2,'ttl':2},{'op':'clear'}]}
        assert process(payload)=={'values':[1,2,1],'loads':2}, 'expiry at boundary and clear'
        assert handle(payload)=={'values':[1,2,1],'loads':2}, 'service cache actions'
    """),
    "atomic-export": code(r"""
        payload = {'previous':'old','records':[{'z':'ø'}],'append':True}
        expected = {'text':'old\n{"z": "ø"}\n','count':1}
        assert process(payload)==expected, 'append separator and UTF-8'
        assert handle(payload)==expected, 'service append'
        rejects(lambda: process({'records':[float('nan')]}))
    """),
    "safe-zip": code(r"""
        payload = {'members':[{'name':'docs/'},{'name':'docs/a.txt','text':'hi'}]}
        expected = {'files':['docs/a.txt'],'contents':{'docs/a.txt':'hi'}}
        assert process(payload)==expected, 'directory entries'
        assert handle(payload)==expected, 'service extraction'
        rejects(lambda: handle({'members':[{'name':'link','text':'target','symlink':True}]}))
    """),
}

QUOTES = {
    "report-columns": ["missing fields; preserve input row order and never mutate or alias input values.",
                       "Validate columns even when rows is empty. Invalid rows/columns raise ValueError."],
    "config-overlay": ["A null value deletes its key, including nested keys; deleting an absent key is a",
                       "via the same merge rules. Reject input containing both config and layers."],
    "retry-policy": ["Only GET and HEAD may retry status 429 or 503 and TimeoutError. All other methods",
                     "Backoff calls sleep(1), sleep(2), ... once before each extra attempt. The final"],
    "cache-expiry": ["Use the injected clock. A finite entry expires when now >= insertion_time + ttl;",
                     "Add Cache.clear() returning the number of stored entries and removing all entries."],
    "atomic-export": ["append=True preserves existing bytes exactly, adding one separating newline only",
                      "UTF-8 with ensure_ascii=False. Accept an iterable and consume it once."],
    "safe-zip": ["empty internal components; Unix symlink members; duplicate file/directory paths",
                 "After validation, extract in archive order and return only relative file names in"],
}


def script(task):
    return PRELUDE + PUBLIC[task]

"""Finite hidden assertions. No candidate-dependent expected values."""
from evaluation.recovery.corpus import code

COMMON = code(r"""
    import copy, io, json, os, subprocess, sys, tempfile, zipfile
    from pathlib import Path
    from app import process
    from service import handle
    results = []
    def check(label, call):
        try:
            call()
            results.append({'label':label,'passed':True})
        except Exception as error:
            results.append({'label':label,'passed':False,'error':type(error).__name__+': '+str(error)})
    def eq(actual, expected):
        assert json.dumps(actual,sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False), (actual,expected)
    def raises(kind, call):
        try: call()
        except kind: return
        raise AssertionError('expected '+kind.__name__)
    def seams(payload, expected):
        original = copy.deepcopy(payload)
        eq(process(payload),expected); eq(handle(payload),expected)
        assert payload==original, 'mutated input'
        command = subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(payload),
            capture_output=True,text=True,timeout=5)
        assert command.returncode==0 and command.stderr=='', command.stderr
        eq(json.loads(command.stdout),expected)
    def compatibility():
        command = subprocess.run([sys.executable,'-B','cli.py','--version'],capture_output=True,text=True,timeout=5)
        assert (command.returncode,command.stdout,command.stderr)==(0,'repo-v1\n','')
        command = subprocess.run([sys.executable,'-B','cli.py','--unknown'],capture_output=True,text=True,timeout=5)
        assert command.returncode==2 and command.stdout==''
        command = subprocess.run([sys.executable,'-B','cli.py'],input='{}',capture_output=True,text=True,timeout=5)
        assert command.returncode==2 and command.stdout=='' and command.stderr.startswith('ERROR:')
    check('CLI compatibility',compatibility)
""")

HIDDEN = {
    "report-columns": code(r"""
        import columns
        check('all seams, order, missing',lambda: seams({'rows':[{'b':2,'a':1},{'a':4}],'columns':['b','a']},[{'b':2,'a':1},{'b':None,'a':4}]))
        check('empty selection',lambda: seams({'rows':[{'q':9}],'columns':[]},[{}]))
        def aliases():
            rows = [{'nested':[{'k':3}]}]
            result = columns.project(rows)
            result[0]['nested'][0]['k']=8
            assert rows==[{'nested':[{'k':3}]}]
            result = columns.project(rows,['nested'])
            result[0]['nested'].append(5)
            assert rows==[{'nested':[{'k':3}]}]
            assert list(columns.project([{'a':1,'b':2}],['b','a'])[0])==['b','a']
        check('API, order and alias freedom',aliases)
        for bad in ('a',[False],[''],['r','r'],{}):
            check('invalid columns '+repr(bad),lambda bad=bad: raises(ValueError,lambda: columns.project([],bad)))
        for bad in ({},[1]):
            check('invalid rows '+repr(bad),lambda bad=bad: raises(ValueError,lambda: columns.project(bad)))
    """),
    "config-overlay": code(r"""
        import settings
        check('all seams recursive replacement',lambda: seams({'layers':[{'a':{'keep':7,'drop':4},'v':[None,1]},{'a':{'drop':None,'new':9},'v':[None,3]}]},
            {'config':{'a':{'keep':7,'new':9},'v':[None,3]}}))
        check('new nested nulls',lambda: eq(settings.merge([{'fresh':{'gone':None,'deep':{'gone':None}}}]),{'fresh':{'deep':{}}}))
        check('type replacement',lambda: eq(settings.merge([{'q':[1]},{'q':{'gone':None,'stay':0}},{'q':False}]),{'q':False}))
        check('legacy service',lambda: seams({'config':{'x':1,'y':None}},{'config':{'x':1}}))
        def aliases():
            layers = [{'a':[{'x':1}]}]
            result = settings.merge(layers); result['a'][0]['x']=5
            assert layers==[{'a':[{'x':1}]}]
        check('no nested aliases',aliases)
        for bad in ({},[None],[{1:2}],[{'list':[{2:3}]}]):
            check('invalid layers '+repr(bad),lambda bad=bad: raises(ValueError,lambda: settings.merge(bad)))
        check('ambiguous payload',lambda: raises(ValueError,lambda: process({'config':{},'layers':[]})))
    """),
    "retry-policy": code(r"""
        import client
        check('HEAD timeout all seams',lambda: seams({'method':'head','retries':2,'responses':['timeout',{'status':429,'body':'wait'},{'status':201,'body':{'id':4}}]},
            {'response':{'status':201,'body':{'id':4}},'attempts':3,'sleeps':[1,2]}))
        check('exhausted response',lambda: seams({'retries':1,'responses':[{'status':503,'body':0},{'status':503,'body':1}]},
            {'response':{'status':503,'body':1},'attempts':2,'sleeps':[1]}))
        def failures():
            for method,kind in [('POST',TimeoutError),('GET',RuntimeError)]:
                calls=[]
                def transport():
                    calls.append(1); raise kind('original')
                raises(kind,lambda: client.fetch(transport,method=method,sleep=lambda n: calls.append(n+10)))
                assert calls==[1]
            calls=[]; sleeps=[]
            def timeout():
                calls.append(1); raise TimeoutError('last')
            raises(TimeoutError,lambda: client.fetch(timeout,retries=2,sleep=sleeps.append))
            assert len(calls)==3 and sleeps==[1,2]
            raises(KeyboardInterrupt,lambda: client.fetch(lambda: (_ for _ in ()).throw(KeyboardInterrupt())))
        check('exception policy and exhaustion',failures)
        def invalid():
            for retries in (True,-1,1.5):
                calls=[]
                raises(ValueError,lambda: client.fetch(lambda: calls.append(1),retries=retries))
                assert calls==[]
            for method in ('',None):
                raises(ValueError,lambda: client.fetch(lambda: None,method=method))
            for response in ({'status':True,'body':0},{'status':99,'body':0},{'status':600,'body':0},{'status':200},[]):
                raises(ValueError,lambda: client.fetch(lambda: response))
            response={'status':204,'body':None}
            assert client.fetch(lambda: response) is response
        check('validation and response identity',invalid)
    """),
    "cache-expiry": code(r"""
        from cache import Cache
        check('action seams',lambda: seams({'actions':[{'op':'get','key':'z','value':4,'at':3,'ttl':0},
            {'op':'get','key':'z','value':6,'at':3,'ttl':0},{'op':'invalidate','key':'z'},{'op':'invalidate','key':'z'},{'op':'clear'}]},
            {'values':[4,6,True,False,0],'loads':2}))
        def temporal():
            now=[10]; calls=[]; cache=Cache(lambda:now[0])
            def loader(): calls.append(1); return {'a':[1]}
            one=cache.get('k',loader,2); one['a'].append(3)
            now[0]=11; two=cache.get('k',loader); assert two=={'a':[1]} and len(calls)==1
            two['a'].append(4); assert cache.get('k',loader)=={'a':[1]}
            now[0]=12; cache.get('k',loader,2); assert len(calls)==2
            now[0]=99; assert cache.invalidate('k') is True
            assert cache.clear()==0
            cache.get('infinite',loader); now[0]=1e6
            cache.get('infinite',loader); assert len(calls)==3
        check('time, hit validation and aliases',temporal)
        def invalid():
            cache=Cache(lambda:0); cache.get('hit',lambda:1)
            for ttl in (True,-1,float('nan'),float('inf'),'2'):
                raises(ValueError,lambda: cache.get('hit',lambda:2,ttl))
            raises(RuntimeError,lambda: cache.get('fail',lambda: (_ for _ in ()).throw(RuntimeError())))
            assert cache.invalidate('fail') is False
            assert cache.get('fail',lambda:9)==9
        check('invalid ttl and loader failure',invalid)
    """),
    "atomic-export": code(r"""
        import exporter
        check('all seams missing append separator',lambda: seams({'previous':'header','records':[{'c':8}],'append':True},
            {'text':'header\n{"c": 8}\n','count':1}))
        check('all seams append newline',lambda: seams({'previous':'{"old": 1}\n','records':[{'b':'雪','a':2}],'append':True},
            {'text':'{"old": 1}\n{"a": 2, "b": "雪"}\n','count':1}))
        def atomicity():
            with tempfile.TemporaryDirectory(dir='.') as folder:
                path=Path(folder)/'data'
                def unchanged(call,kind=ValueError):
                    path.write_bytes(b'original\xff')
                    raises(kind,call)
                    assert path.read_bytes()==b'original\xff'
                    assert sorted(p.name for p in Path(folder).iterdir())==['data']
                for bad in ([],{'x':float('inf')},{'x':object()}):
                    unchanged(lambda: exporter.write_records(path,iter([{'ok':1},bad])))
                def broken():
                    yield {'ok':2}; raise RuntimeError('iteration')
                unchanged(lambda: exporter.write_records(path,broken()),RuntimeError)
                reject_replace = [True]
                def audit(event,args):
                    if reject_replace[0] and event=='os.rename': raise OSError('replace')
                sys.addaudithook(audit)
                try: unchanged(lambda: exporter.write_records(path,[{'ok':3}]),OSError)
                finally: reject_replace[0] = False
                path.unlink()
                raises(ValueError,lambda: exporter.write_records(path,[None]))
                assert list(Path(folder).iterdir())==[]
                path.write_bytes(b'unchanged')
                assert exporter.write_records(path,[],append=True)==0 and path.read_bytes()==b'unchanged'
                path.unlink()
                assert exporter.write_records(path,iter([{'x':1}]),append=True)==1
                assert path.read_bytes()==b'{"x": 1}\n'
        check('rollback, replace failure, cleanup and missing append',atomicity)
    """),
    "safe-zip": code(r"""
        import archive
        check('all seams archive order',lambda: seams({'members':[{'name':'b/c.txt','text':'c'},{'name':'a.txt','text':'a'}]},
            {'files':['b/c.txt','a.txt'],'contents':{'b/c.txt':'c','a.txt':'a'}}))
        def packed(names):
            data=io.BytesIO()
            with zipfile.ZipFile(data,'w') as out:
                for name in names: out.writestr(name.replace('\0','X'),'payload')
            result = data.getvalue()
            for name in names:
                if '\0' in name: result = result.replace(name.replace('\0','X').encode(),name.encode())
            return result
        def rejection():
            with tempfile.TemporaryDirectory(dir='.') as folder:
                target=Path(folder)/'out'
                for name in ('../escape','/abs','C:drive','a\\b','a//b','a/./b','a/../b','nul\0hidden'):
                    raises(ValueError,lambda: archive.extract(packed(['safe/file',name]),target))
                    assert not target.exists()
                for names in (['f','f'],['d/','d/'],['d/','d'],['f/child','f']):
                    raises(ValueError,lambda: archive.extract(packed(names),target))
                    assert not target.exists()
                target.mkdir(); (target/'keep').write_text('old')
                (target/'link').symlink_to((target/'keep').resolve())
                raises(ValueError,lambda: archive.extract(packed(['safe/file','link']),target))
                assert (target/'keep').read_text()=='old' and not (target/'safe').exists()
                outside=Path(folder)/'outside'; outside.mkdir()
                (target/'dirlink').symlink_to(outside.resolve(),target_is_directory=True)
                raises(ValueError,lambda: archive.extract(packed(['dirlink/new']),target))
                assert list(outside.iterdir())==[]
                raises(ValueError,lambda: archive.extract(packed(['new']),target/'dirlink'))
                assert archive.extract(packed([]),target)==[]
                assert archive.extract(packed(['keep']),target)==['keep']
                assert (target/'keep').read_text()=='payload'
        check('unsafe manifest, duplicates and destination symlinks',rejection)
        check('symlink member',lambda: raises(ValueError,lambda: process({'members':[{'name':'shortcut','text':'elsewhere','symlink':True}]})))
    """),
}


def script(task):
    return COMMON + HIDDEN[task] + code(r"""
        import app
        tests = subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(Path(app.__file__).parent/'tests')],
            capture_output=True,text=True,timeout=10)
        print(json.dumps({'cases':results,'repository_tests_passed':tests.returncode==0},sort_keys=True))
    """)

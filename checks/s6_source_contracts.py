"""Exposed source-contract feasibility fixtures; no private grader answers enter contracts."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6
from checks.s6_utc_references import EFFECTIVE
from checks import metamorphic
p=s6.p

IMPORT = '''import sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root))
import product
'''

PAGINATION = IMPORT + '''import copy, itertools
from decimal import Decimal
from enum import IntEnum
class Rank:
    def __init__(self,value): self.value=value
    def __eq__(self,other): return isinstance(other,Rank) and self.value==other.value
    def __lt__(self,other): return self.value<other.value
    def __gt__(self,other): return self.value>other.value
def full(rows):
    data={'rows':rows,'offset':0,'limit':len(rows)}
    before=copy.deepcopy(data)
    value=product.process(data)
    assert data==before, 'input mutation'
    assert isinstance(value,list) and len(value)==len(rows), 'row loss or wrong result shape'
    assert sorted(r['marker'] for r in value)==sorted(r['marker'] for r in rows), 'row multiplicity'
    for row in value:
        assert row==next(r for r in rows if r['marker']==row['marker']), 'field change'
    for left,right in zip(value,value[1:]):
        assert not right['score']>left['score'], 'descending score order'
        if left['score']==right['score']: assert not right['id']<left['id'], 'ascending ID tie order'
    return value
for scores in ([2,2,-1],['b','b','a'],[Decimal('2'),Decimal('2'),Decimal('-1')],
               [Rank(2),Rank(2),Rank(-1)]):
    rows=[{'id':ident,'score':score,'marker':i,'other':[i]} for i,(ident,score) in enumerate(zip(['b','a','c'],scores))]
    for permutation in itertools.permutations(rows):
        rows=list(permutation); ordered=full(rows)
        for offset,limit in itertools.product(range(5),repeat=2):
            for cast in (int,lambda v:IntEnum('Page',{'value':v}).value):
                data={'rows':rows,'offset':cast(offset),'limit':cast(limit)}
                before=copy.deepcopy(data)
                assert product.process(data)==ordered[offset:offset+limit], 'slice or integer-subclass narrowing'
                assert data==before, 'paging mutates input'
full([])
full([{'id':1,'score':2,'marker':0},{'id':'a','score':1,'marker':1}])
for field in ('offset','limit'):
    for invalid in (-1,True,False,1.5,'1'):
        data={'rows':[],'offset':0,'limit':0};data[field]=invalid
        try: product.process(data)
        except Exception: pass
        else: raise AssertionError('nonnegative nonboolean integer paging required')
for row in ({'id':'only'},{'score':1}):
    try: product.process({'rows':[row],'offset':0,'limit':1})
    except Exception: pass
    else: raise AssertionError('row must contain id and score, including singleton rows')
'''

# Source-valid examples authored for this relation, not copied from grader inputs.
PAGINATION += metamorphic.representation_probe('product','process',
    [['rows','*','score'],['rows','*','id'],['offset'],['limit']],
    [{'rows':[{'id':ident,'score':score,'other':[index]} for index,(ident,score) in enumerate(rows)],
      'offset':offset,'limit':limit}
     for rows in ([('gamma',7),('alpha',7),('beta',3)],
                  [(1,7),('alpha',3)], [('gamma','p'),('alpha','p'),('beta','f')])
     for offset,limit in ((0,3),(1,1),(5,2),(0,0))],['ordering','ordering','integer','integer'])

USERNAME = IMPORT + '''import itertools
white=set(range(9,14))|{32,133,160,5760}|set(range(8192,8203))|{8232,8233,8239,8287,12288}
def check(value):
    if not value or all(ord(c) in white for c in value):
        try: product.process(value)
        except ValueError: return
        raise AssertionError('empty or Unicode White_Space-only string must raise ValueError')
    assert product.process(value)==value, 'valid username changed or rejected'
check('')
for point in range(sys.maxunicode+1): check(chr(point))
characters=[chr(point) for point in white]
for pair in itertools.product(characters,repeat=2): check(''.join(pair))
for padding in characters:
    for content in ('name','\\u200b','\\u001c','\\U0001f600'):
        check(padding+content+padding)
'''

USERNAME += metamorphic.representation_probe('product','process',[[]],
    ['alpha','  alpha  ','\u200b','\u001c','', '\u0085\u2003'],['text'])

UTC_LEAP = IMPORT + '''# An actual UTC leap-second instant, established by IERS Bulletin C 52.
# This is an identity/representation invariant, not a Python parser-derived answer.
value='2016-12-31T23:59:60Z'
assert product.process(value)==value, 'valid UTC instant must retain its instant in requested UTC format'
'''

UTC = UTC_LEAP + '''from datetime import date, datetime, timedelta
from fractions import Fraction
# Generate equivalent representations and offsets independently of the candidate parser.
for point in (date(1999,12,31),date(2000,2,29),date(2001,1,1),date(2400,2,29)):
    iso=point.isocalendar();ordinal=(point-date(point.year,1,1)).days+1
    extended=[point.isoformat(),f'{point.year:04}-{ordinal:03}',f'{iso.year:04}-W{iso.week:02}-{iso.weekday}']
    basic=[point.strftime('%Y%m%d'),f'{point.year:04}{ordinal:03}',f'{iso.year:04}W{iso.week:02}{iso.weekday}']
    for style,forms in ((True,extended),(False,basic)):
        for parts in ([12],[12,30],[12,30,45]):
            for decimal in ('.',','):
                for numerator,denominator in ((5,10),(125,1000)):
                    digits=str(numerator).zfill(len(str(denominator))-1)
                    clock=(':'.join(f'{x:02}' for x in parts) if style else ''.join(f'{x:02}' for x in parts))+decimal+digits
                    unit=(3600,60,1)[len(parts)-1]
                    seconds=sum(x*u for x,u in zip(parts,(3600,60,1)))+int(Fraction(numerator,denominator)*unit)
                    for offset in (-345,0,330):
                        zone='Z' if not offset else ('+' if offset>0 else '-')+f'{abs(offset)//60:02}'+(':' if style else '')+f'{abs(offset)%60:02}'
                        expected=(datetime(point.year,point.month,point.day)+timedelta(seconds=seconds-offset*60)).isoformat()+'Z'
                        for form in forms:assert product.process(form+'T'+clock+zone)==expected, 'representation, fractional-unit or offset narrowing'
        for form in forms:
            clock='24:00:00' if style else '240000'
            assert product.process(form+'T'+clock+'Z')==(point+timedelta(days=1)).isoformat()+'T00:00:00Z'
# Preserved formatting has no undocumented Python year-range restriction.
for year in (0,1,400,9999):
    value=f'{year:04}-01-01T00:00:00Z'
    assert product.process(value)==value, 'year domain or padding restriction'
for width in (4,5,6,7,10,30):
    year='2024'.zfill(width)
    for value in ('+'+year+'-04-01T00:00:00Z','+'+year+'0401T000000Z',
                  '+'+year+'W141T000000Z'):
        assert product.process(value)=='2024-04-01T00:00:00Z', 'unambiguous year-width narrowing'
for value in ('+0020240101T000000Z','+00020240101T000000Z','+0000010101T000000Z'):
    try:product.process(value)
    except ValueError:pass
    else:raise AssertionError('ambiguous date silently assigned a year width')
''' + '\n# Public IERS leap-second effective dates, not private grader answers.\nfor effective in '+repr(EFFECTIVE)+''':
    next_day=date.fromisoformat(effective);point=next_day-timedelta(days=1)
    leap=point.isoformat()+'T23:59:60Z'
    for width in (5,6,7,10):
        value='+'+str(point.year).zfill(width)+f'{point.month:02}{point.day:02}T235960Z'
        assert product.process(value)==leap, 'date-only ambiguity must be resolved against complete timestamp validity'
    for unit,length,clock in ((60,61,'23:59'),(3600,3601,'23')):
        for digits in ('5','99','9999'):
            elapsed=int(Fraction(int(digits),10**len(digits))*length)
            start=datetime(point.year,point.month,point.day,23,59 if unit==60 else 0)
            expected=leap if elapsed==unit else (start+timedelta(seconds=elapsed)).isoformat()+'Z'
            for style in (True,False):
                form=point.isoformat() if style else f'{point.year:04}{point.month:02}{point.day:02}'
                time=clock if style else clock.replace(':','')
                assert product.process(form+'T'+time+'.'+digits+'Z')==expected, 'fraction used nominal duration for leap-modified clock unit'
# ISO graphic symbols retain their meaning through Unicode JSON interchange.
for form in ('2024-02-29','2024-02-29'.replace('-','\\u2010'),'20240229'):
    style='-' in form or '\\u2010' in form
    clock='23:30:00' if style else '233000'
    zone='\\u221201:00' if style else '\\u22120100'
    assert product.process(form+'T'+clock+zone)=='2024-03-01T00:30:00Z', 'graphic minus/hyphen narrowing'
for invalid in ('2023-366T00:00:00Z','2021-W53-1T00:00:00Z','2024-02-30T00:00:00Z',
                '2024-01-01T00:00:00','2024-01-01T24:00:01Z','2024-01-01T12.5:30Z',
                '2016-12-30T23:59:60Z','2024-01-01T00:00:00+01:02:03',
                '2024-01-01T00:00:00-00:00','20240101T000000-00'):
    try:product.process(invalid)
    except (ValueError,KeyError,TypeError):pass
    else:raise AssertionError('malformed timestamp accepted')
'''

INTERVALS = IMPORT + '''import copy, itertools
def check(data):
    before=copy.deepcopy(data)
    value=product.process(data)
    assert data==before, 'input mutation'
    if not data: assert value==[], 'empty interval result'
    assert all(len(pair)==2 and pair[0]<=pair[1] for pair in value)
    assert all(left[1]<right[0] for left,right in zip(value,value[1:])), 'overlap or touching segments unmerged'
    for point in range(-4,5):
        expected=any(2*a<=point<=2*b for a,b in data)
        assert any(2*a<=point<=2*b for a,b in value)==expected, 'changed continuous interval coverage'
    endpoints={x for pair in data for x in pair}
    assert all(x in endpoints for pair in value for x in pair), 'invented endpoint'
segments=[(a,b) for a in range(-2,3) for b in range(a,3)]
for length in range(4):
    for values in itertools.product(segments,repeat=length): check([list(pair) for pair in values])
for a,b in itertools.product(range(-2,3),repeat=2):
    if a<=b: continue
    try: product.process([[a,b]])
    except Exception: pass
    else: raise AssertionError('reversed interval accepted')
'''

CLI = '''import json, subprocess, sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
def run(*args):
    return subprocess.run([sys.executable,'-I','-B',str(root/'app.py'),*args],cwd=Path.cwd(),
                          capture_output=True,text=True,timeout=8)
r=run('--version')
assert (r.returncode,r.stdout,r.stderr)==(0,'pilot-tool 1.0\\n','')
for args in ((),('{}','{}'),('{',)):
    r=run(*args)
    assert r.returncode==2 and not r.stdout and r.stderr.strip(), 'preserved argument error channels'
# Exercise the candidate adapter's named exception mapping without guessing a product payload.
# The substitute callable checks the adapter only; R1 independently checks the real product.
import types, runpy, contextlib, io
for error_type in (ValueError,KeyError,TypeError):
    stub=types.ModuleType('product')
    def raises(data): raise error_type('source-contract exception observation')
    stub.process=raises
    original=sys.modules.get('product');argv=sys.argv
    sys.modules['product']=stub;sys.argv=[str(root/'app.py'),'null']
    out,err=io.StringIO(),io.StringIO()
    try:
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            try: runpy.run_path(str(root/'app.py'),run_name='__main__')
            except SystemExit as exit: assert exit.code==2
            else: raise AssertionError('CLI did not exit with named error status')
        assert not out.getvalue() and err.getvalue().strip()
    finally:
        sys.argv=argv
        if original is None: sys.modules.pop('product',None)
        else: sys.modules['product']=original
'''

CONSTRAINTS = '''import ast, hashlib, subprocess, sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
files=[path for path in root.rglob('*') if path.is_file() and '.git' not in path.relative_to(root).parts]
before={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
local={path.stem for path in root.glob('*.py')}|{path.name for path in root.iterdir() if path.is_dir()}
for path in root.rglob('*.py'):
    for node in ast.walk(ast.parse(path.read_text())):
        names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.level==0 and node.module else []
        assert all(name.split('.')[0] in sys.stdlib_module_names|local for name in names), 'foreign dependency'
sys.path.insert(0,str(root))
import product
assert callable(product.process)
r=subprocess.run([sys.executable,'-I','-B',str(root/'app.py'),'--version'],capture_output=True,text=True,timeout=8)
assert (r.returncode,r.stdout,r.stderr)==(0,'pilot-tool 1.0\\n','')
after={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob('*') if path.is_file() and '.git' not in path.relative_to(root).parts}
assert before==after, 'product/source mutation'
# Finite observations supplement native isolation and independent source/code review.
'''


UTC += metamorphic.representation_probe('product','process',[[]],
    ['2024-03-01T00:30:00Z','2016-12-31T23:59:60Z','bad',
     '+0020240101T000000Z'],['text'])


def contract(task, source, base_tree):
    """Explicit interpretations need independent adjudication; this never grants approval."""
    r1={
        'stable-pagination':(PAGINATION,
            ['Rows contain id and score; scores have a well-defined descending order, including sortable strings and public-library comparable values.',
             'Sorting uses the ordering protocol; equality and greater-than operations need not exist. Compare IDs only within ordering-equivalent score groups; preserve fields and multiplicity.',
             'Paging accepts nonnegative integer instances, including nonboolean subclasses; booleans and other values are invalid.'],
            ['Result rows are ordered by descending score and ascending ID only on score ties.',
             'Each output row retains its fields; full results retain all rows; pages are the requested slice.',
             'Inputs are unchanged; missing row fields and invalid paging are rejected.']),
        'unicode-usernames':(USERNAME,
            ['The public library argument is the whole username string; the CLI JSON string is decoded to it and the returned string serialized directly.',
             'All username strings except empty/Unicode White_Space-only are preserved, including characters outside that property.'],
            ['Empty or all-White_Space strings raise ValueError, including subclasses of that exception.',
             'Every other string retains its characters without trimming or normalization.']),
        'utc-timestamps':(UTC,
            ['The public library argument is the whole timestamp string; all source-promised ISO representations remain in scope, including valid leap-second instants.',
             'Complete calendar, ordinal and week dates; consistent basic/extended forms; reduced time precision and decimal fractions of the lowest included unit.',
             'Z and signed hour/minute offsets; end-of-day rollover; Gregorian year padding and expansion without a Python date-range restriction.',
             'Ambiguity is tested on the complete timestamp after time validity; fractions use the actual leap-modified clock-unit duration.',
             'Leap-second validity uses public IERS announcements, currently Bulletin C 72. This time-dependent public fact is frozen study context, not private oracle data.'],
            ['Conversion preserves the UTC instant and produces the requested UTC representation; fractional subsecond precision is truncated.']),
        'interval-union':(INTERVALS,
            ['Lists of integer endpoint pairs, including overlaps, touching pairs, zero-length pairs and empty input; reversed pairs are rejected.'],
            ['Result is sorted and merged, preserving precisely the covered continuous points and original endpoints without input mutation.']),
    }[task]
    payloads={
        'stable-pagination':[{'rows':[{'id':'b','score':'a','other':'kept'},{'id':'a','score':'b'}],'offset':0,'limit':2}],
        'unicode-usernames':[' name ','\u200b'],
        'utc-timestamps':['2017-01-01T01:00:00+01:00'],
        'interval-union':[[[-2,2],[0,1]],[]],
    }[task]
    cli=CLI+IMPORT+'import copy, json\nfor data in '+repr(payloads)+''':
    expected=product.process(copy.deepcopy(data))
    observed=run(json.dumps(data,ensure_ascii=True))
    assert observed.returncode==0 and not observed.stderr
    assert json.loads(observed.stdout)==expected, 'CLI/library payload or result mapping changed'
'''
    rows=[]
    for ident,probe,domains,invariants in [
        ('R1',*r1),
        ('R2',cli,['Original JSON argument/serialization/error adapter and version.'],
         ['Version and argument error behavior remain unchanged; named exception classes map to exit 2, explanatory stderr and no stdout.']),
        ('R3',CONSTRAINTS,['All implementations and public library/CLI paths; architecture is unrestricted.'],
         ['Standard library only; no network, external effects or input/source mutation; public interfaces preserved.'])]:
        quote=next(line for line in source.splitlines() if line.startswith(ident+':'))
        rows.append({'id':ident,'source_quote':quote,'domains':domains,'invariants':invariants,'probe':probe})
    return {'format':'source-evidence-v1','source_sha256':p.host.sha256(source.encode()),'base_tree':base_tree,
            'interface':'Original app.py passes its sole decoded JSON argument to product.process(data), serializing its return. '+
                ('Pagination consumes the complete object containing rows, offset and limit.' if task=='stable-pagination' else
                 'The interval list is the complete argument and resulting interval list the complete result.' if task=='interval-union' else
                 'The scalar string is the complete process argument and scalar result; this follows the original baseline public behavior and R1.'),
            'criteria':rows,'unresolved':[
                'Expanded-year ambiguity needs the actual user clarification retained in the source.'
            ] if task=='utc-timestamps' and 'Ambiguous timestamp strings without an interchange agreement raise ValueError' not in source else []}

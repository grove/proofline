"""Compile source-declared representation relations, without expected task answers."""
import json


def representation_probe(module, function, paths, samples, protocols):
    """A nonmutating unary interface preserves source-declared value representations.

    The caller must establish this relation from the source, not from candidate
    behavior. Samples exercise the relation; they do not establish source coverage.
    """
    if (not isinstance(module, str) or not all(part.isidentifier() for part in module.split('.'))
            or not isinstance(function, str) or not function.isidentifier()
            or not isinstance(paths, list) or not 1 <= len(paths) <= 6
            or any(not isinstance(path, list) or
                   any(not isinstance(key, (str, int)) or isinstance(key, bool) for key in path) for path in paths)
            or not isinstance(protocols, list) or len(protocols)!=len(paths)
            or any(protocol not in ('ordering','text','integer') for protocol in protocols)
            or not isinstance(samples, list) or not samples):
        raise ValueError('Representation relation needs an interface, bounded typed paths and source-valid samples')
    declaration = json.dumps({'module': module, 'function': function, 'paths': paths,
                              'samples': samples,'protocols':protocols}, ensure_ascii=True, allow_nan=False)
    return 'relation = ' + repr(declaration) + '\n' + REPRESENTATIONS


REPRESENTATIONS = '''import copy, importlib, itertools, json, sys
sys.path.insert(0,sys.argv[1])
relation=json.loads(relation)
operation=getattr(importlib.import_module(relation['module']),relation['function'])
class MinimalOrder:
    def __init__(self,value): self.value=value
    def __lt__(self,other):
        return self.value < (other.value if isinstance(other,MinimalOrder) else other)
class EqualityUnavailable(MinimalOrder):
    def __eq__(self,other): raise TypeError('equality is unavailable for a source ordering domain')
class NoConvenienceText(str):
    def __getattribute__(self,name):
        if not name.startswith('__') and name in str.__dict__:
            raise TypeError('optional instance text method is unavailable: '+name)
        return str.__getattribute__(self,name)
class NoIteratorText(str):
    def __iter__(self): raise TypeError('optional instance text iteration is unavailable')
class NoIntegerOperators(int):
    def __lt__(self,other): raise TypeError('optional instance integer comparison is unavailable')
    def __add__(self,other): raise TypeError('optional instance integer addition is unavailable')
class NoIntegerConversion(int):
    def __int__(self): raise TypeError('optional instance integer conversion is unavailable')
def replace(value,path,wrapper):
    if not path: return wrapper(value)
    key,*rest=path
    if key=='*':
        if isinstance(value,list): return [replace(item,rest,wrapper) for item in value]
        if isinstance(value,dict): return {key:replace(item,rest,wrapper) for key,item in value.items()}
        raise AssertionError('source-declared wildcard does not match a collection')
    value[key]=replace(value[key],rest,wrapper)
    return value
def normalize(value):
    if isinstance(value,MinimalOrder): return normalize(value.value)
    if isinstance(value,dict): return {key:normalize(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)): return [normalize(item) for item in value]
    return value
def observed(value):
    before=json.dumps(normalize(value),sort_keys=True,allow_nan=False)
    try: result={'returned':normalize(operation(value))}
    except Exception as error:
        result={'error':next((kind.__name__ for kind in (ValueError,KeyError,TypeError)
                             if isinstance(error,kind)),type(error).__name__)}
    assert json.dumps(normalize(value),sort_keys=True,allow_nan=False)==before, 'representation probe mutated input'
    return json.dumps(result,sort_keys=True,allow_nan=False)
families={'ordering':(None,MinimalOrder,EqualityUnavailable),
          'text':(None,NoConvenienceText,NoIteratorText),
          'integer':(None,NoIntegerOperators,NoIntegerConversion)}
for sample in relation['samples']:
    baseline=observed(copy.deepcopy(sample))
    # Vary each declared field independently, including mixed protocol choices.
    for wrappers in itertools.product(*(families[protocol] for protocol in relation['protocols'])):
        value=copy.deepcopy(sample)
        for path,wrapper in zip(relation['paths'],wrappers):
            if wrapper is not None: value=replace(value,path,wrapper)
        assert observed(value)==baseline, 'source-declared representation changed the result or error family'
'''

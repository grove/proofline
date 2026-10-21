import json
import warnings
from itsdangerous import BadSignature, SignatureExpired, URLSafeSerializer, URLSafeTimedSerializer

cases = []
def check(label, run):
    try:
        run()
        cases.append({"label": label, "passed": True})
    except Exception as error:
        cases.append({"label": label, "passed": False, "error": repr(error)})

def untimed():
    s = URLSafeSerializer('SECRET')
    signed = s.dumps('value')
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter('always')
        try:
            s.loads(signed, max_age=-1)
        except Exception:
            return  # Original request allows an error or warning, not a specific class.
        assert observed, 'max_age silently ignored'

def timed():
    s = URLSafeTimedSerializer('SECRET')
    signed = s.dumps('value')
    try:
        s.loads(signed, max_age=-1)
    except SignatureExpired:
        pass
    else:
        raise AssertionError('expired timed token accepted')
    assert s.loads(signed, max_age=60) == 'value'
    assert s.loads(signed, return_timestamp=True)[0] == 'value'

def compatibility():
    s = URLSafeSerializer(['old', 'SECRET'], salt='custom')
    signed = s.dumps({'value': 1})
    assert s.loads(signed) == {'value': 1}
    assert s.loads_unsafe(signed) == (True, {'value': 1})
    try:
        URLSafeSerializer('wrong', salt='custom').loads(signed)
    except BadSignature:
        pass
    else:
        raise AssertionError('invalid signature accepted')

check('untimed-max-age-error-or-warning', untimed)
check('timed-expiry-and-timestamp-compatibility', timed)
check('salt-key-and-invalid-signature-compatibility', compatibility)
print(json.dumps({'cases': cases}))
assert all(c['passed'] for c in cases)

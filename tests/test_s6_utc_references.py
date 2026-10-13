"""UTC controls are checked against independent arithmetic and public observations."""
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from checks import s6_utc_references as references, s6_iso_audit, s6_corpus, s6_source_contracts


class UtcReferences(unittest.TestCase):
    def test_public_properties_pass_both_structures_without_private_answers(self):
        for variant in ('good','alternative'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);product=root/'candidate';product.mkdir()
                (product/'product.py').write_text(references.program(variant))
                script=root/'properties.py';script.write_text(s6_source_contracts.UTC)
                result=subprocess.run([sys.executable,'-I','-B',str(script),str(product)],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_both_controls_cover_preserved_and_new_source_readback(self):
        item=next(x for x in s6_corpus.TASKS if x['id']=='utc-timestamps')
        probes=[(x['input'],x['expected']) for x in item['probes']]
        probes += [(x,y) for x,y,_ in s6_iso_audit.PROBES]
        probes += [('0000-02-29T00:00:00Z','0000-02-29T00:00:00Z'),
                   ('0001-01-01T00:00:00+01:00','0000-12-31T23:00:00Z'),
                   ('9999-12-31T23:00:00-01:00','+010000-01-01T00:00:00Z'),
                   ('-000001-12-31T24:00:00Z','0000-01-01T00:00:00Z'),
                   ('+010000-001T00:00:00Z','+010000-01-01T00:00:00Z')]
        probes += [('2024-02-29T23:30:00\u221201:00','2024-03-01T00:30:00Z'),
                   ('20240229T233000\u22120100','2024-03-01T00:30:00Z'),
                   ('2024\u201002\u201029T23:30:00\u221201:00','2024-03-01T00:30:00Z'),
                   ('\u2212000001-12-31T24:00:00Z','0000-01-01T00:00:00Z')]
        probes += [(value,'2016-12-31T23:59:60Z') for value in (
            '+0020161231T235960Z','+0020170101T005960+0100','+020161231T235960.5Z',
            '2016-12-31T23:59.99Z','20161231T2359,99Z',
            '2017-01-01T00:59.99+01:00','20161231T23.9999Z',
            '2016-12-31T23:59:60.9999Z')]
        probes += [('2016-12-31T23:59.5Z','2016-12-31T23:59:30Z'),
                   ('2017-01-01T00.9+00:15','2017-01-01T00:38:59Z')]
        bad=['2024-02-30T00:00:00Z','2023-366T00:00:00Z','2021-W53-1T00:00:00Z',
             '2016-12-30T23:59:60Z','2016-12-31T22:59:60Z','2024-01-01T24:00:01Z',
             '2024-01-01T24.1Z','2024-01-01T12.5:30Z','2024-01-01T00:00:00+24:00',
             '2024-01-01T00:00:00+01:60','2024-01-01T00:00:00+0100',
             '20240101T00:00:00Z','2024-01-01T000000Z','2024-01-01T00:00:00Z\n',None]
        bad += ['2024\u221202\u221229T00:00:00Z','2024-02-29T23:30:00\u201001:00']
        bad += ['+0020240101T000000Z','+00020240101T000000Z',
                '+0020161231T235959Z',
                '2024-01-01T00:00:00-00:00','20240101T000000-00','-0000-01-01T00:00:00Z']
        for width in (4,5,6,7,10,30):
            year='2024'.zfill(width)
            probes += [('+'+year+'0401T000000Z','2024-04-01T00:00:00Z'),
                       ('+'+year+'W141T000000Z','2024-04-01T00:00:00Z')]
        for variant in ('good','alternative'):
            module={};exec(references.program(variant),module);process=module['process']
            for value,expected in probes:
                with self.subTest(variant=variant,value=value):
                    if isinstance(expected,dict):
                        with self.assertRaises((ValueError,KeyError,TypeError)):process(value)
                    else:self.assertEqual(process(value),expected)
            for value in bad:
                with self.subTest(variant=variant,invalid=value):
                    errors=ValueError if value in ('+0020240101T000000Z','+00020240101T000000Z','+0020161231T235959Z') else (ValueError,KeyError,TypeError)
                    with self.assertRaises(errors):process(value)

    def test_calendar_arithmetic_matches_an_independent_gregorian_cycle(self):
        point=date(2000,1,1);number=references.day_number(2000,1,1)
        for offset in range(146097):
            actual=point+timedelta(days=offset)
            self.assertEqual(references.civil(number+offset),(actual.year,actual.month,actual.day))
            self.assertEqual(references.day_number(actual.year,actual.month,actual.day),number+offset)
        for year in (-10000,-400,-1,0,9999,10000):
            self.assertEqual(references.civil(references.day_number(year,3,1)),(year,3,1))

    def test_both_structures_preserve_date_forms_and_non_hour_offset_arithmetic(self):
        programs=[]
        for variant in ('good','alternative'):
            module={};exec(references.program(variant),module);programs.append(module['process'])
        for year in range(2000,2400):
            for month,day in ((1,1),(3,1),(12,31)):
                point=date(year,month,day);iso=point.isocalendar()
                ordinal=(point-date(year,1,1)).days+1
                forms=[f'{year:04}-{month:02}-{day:02}',f'{year:04}-{ordinal:03}',f'{iso.year:04}-W{iso.week:02}-{iso.weekday}']
                for h in (-23,-5,0,5,23):
                    minutes=h*60+(15 if h>=0 else -15)
                    sign='+' if minutes>=0 else '-';oh,om=divmod(abs(minutes),60)
                    expected=point-timedelta(days=1) if minutes>0 else point
                    hh,mm=divmod((-minutes)%1440,60)
                    target=f'{expected.isoformat()}T{hh:02}:{mm:02}:00Z'
                    for form in forms:
                        for process in programs:self.assertEqual(process(form+f'T00:00:00{sign}{oh:02}:{om:02}'),target)

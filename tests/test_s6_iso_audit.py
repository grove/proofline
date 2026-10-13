"""Audit fixtures independently convert decimal hour/minute units before truncation."""
from fractions import Fraction
import unittest

from checks import s6_iso_audit as audit


class IsoAudit(unittest.TestCase):
    def test_fraction_expectations_follow_unit_arithmetic(self):
        expected={value:result for value,result,_ in audit.PROBES}
        hour=Fraction('12.9999')*3600
        h,remainder=divmod(int(hour),3600);m,s=divmod(remainder,60)
        self.assertEqual(expected['2024-02-29T12.9999Z'],f'2024-02-29T{h:02}:{m:02}:{s:02}Z')
        self.assertEqual(Fraction('0.5')*3600,30*60)
        self.assertEqual(Fraction('0.5')*60,30)
        self.assertEqual(expected['2024-02-29T12.5Z'],'2024-02-29T12:30:00Z')
        self.assertEqual(expected['20240229T1230.5Z'],'2024-02-29T12:30:30Z')

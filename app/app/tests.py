from django.test import SimpleTestCase
from app import calc

class CalcTest(SimpleTestCase):

    def test_add_numbers(self):
        res = calc.add(1,2)
        self.assertEqual(res, 3)

    def test_subtract_number(self):
        res = calc.subract(5, 3)
        self.assertEqual(res, 2)
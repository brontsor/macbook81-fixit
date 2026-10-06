import unittest
from datetime import date, timedelta

from macbook81_fixit.age import format_age, manufacture_date


class TestAge(unittest.TestCase):
    def test_2015_first_half_week_12(self):
        built = manufacture_date("C02PF0000000")
        self.assertEqual(built, date(2015, 1, 1) + timedelta(days=11 * 7))

    def test_2015_second_half_week_27(self):
        built = manufacture_date("C02Q10000000")
        self.assertEqual(built, date(2015, 1, 1) + timedelta(days=26 * 7))

    def test_a_year_outside_this_model_is_unknown(self):
        self.assertIsNone(manufacture_date("C02CF0000000"))

    def test_week_53_only_in_the_second_half(self):
        self.assertIsNone(manufacture_date("C02PY0000000"))
        self.assertEqual(
            manufacture_date("C02QY0000000"),
            date(2015, 1, 1) + timedelta(days=52 * 7),
        )

    def test_age_is_years_and_months_and_hides_the_serial(self):
        text = format_age(date(2015, 3, 19), date(2026, 10, 6))
        self.assertEqual(text, "11 years, 6 months")
        self.assertNotIn("C02", text)

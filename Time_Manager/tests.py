from datetime import date
import calendar

from django.test import TestCase

from .date_utils import add_ordinal_suffix, parse_day, parse_month, parse_partial_date


class ParseMonthTests(TestCase):
    def test_accepts_full_and_short_names_case_insensitively(self):
        self.assertEqual(parse_month("Feb"), 2)
        self.assertEqual(parse_month("february"), 2)
        self.assertEqual(parse_month("MAY"), 5)
        self.assertEqual(parse_month("december"), 12)
        self.assertEqual(parse_month("Jan"), 1)
        self.assertEqual(parse_month("Sep"), 9)

    def test_accepts_unambiguous_short_abbreviations(self):
        self.assertEqual(parse_month("Mar"), 3)
        self.assertEqual(parse_month("Apr"), 4)
        self.assertEqual(parse_month("Aug"), 8)

    def test_accepts_numeric_input(self):
        self.assertEqual(parse_month(2), 2)
        self.assertEqual(parse_month("2"), 2)

    def test_rejects_out_of_range_numeric_month(self):
        with self.assertRaises(ValueError):
            parse_month("13")

    def test_rejects_ambiguous_single_letter_input(self):
        # "M" could mean March or May - the function should refuse to guess.
        with self.assertRaises(ValueError):
            parse_month("M")
        # "J" could mean January, June, or July.
        with self.assertRaises(ValueError):
            parse_month("J")


class ParseDayTests(TestCase):
    def test_accepts_plain_and_ordinal_numbers(self):
        self.assertEqual(parse_day("15"), 15)
        self.assertEqual(parse_day("15th"), 15)
        self.assertEqual(parse_day("1st"), 1)
        self.assertEqual(parse_day("22nd"), 22)
        self.assertEqual(parse_day("31st"), 31)

    def test_accepts_integer_input(self):
        self.assertEqual(parse_day(5), 5)

    def test_rejects_out_of_range_day(self):
        with self.assertRaises(ValueError):
            parse_day("32")

    def test_rejects_day_of_week_names(self):
        # Day-of-week names are intentionally not accepted here - the field
        # wants a specific date number, not "Tuesday".
        with self.assertRaises(ValueError):
            parse_day("Tue")
        with self.assertRaises(ValueError):
            parse_day("Mon")


class AddOrdinalSuffixTests(TestCase):
    def test_common_suffixes(self):
        cases = {
            1: "1st", 2: "2nd", 3: "3rd", 4: "4th",
            21: "21st", 22: "22nd", 23: "23rd", 24: "24th",
        }
        for day, expected in cases.items():
            self.assertEqual(add_ordinal_suffix(day), expected)

    def test_eleven_twelve_thirteen_are_th_not_st_nd_rd(self):
        self.assertEqual(add_ordinal_suffix(11), "11th")
        self.assertEqual(add_ordinal_suffix(12), "12th")
        self.assertEqual(add_ordinal_suffix(13), "13th")


class ParsePartialDateTests(TestCase):
    def test_year_only_fills_in_todays_month_and_day(self):
        today = date.today()
        result = parse_partial_date(year=2026)
        self.assertEqual(result, date(2026, today.month, today.day))

    def test_year_and_month_fills_in_todays_day(self):
        today = date.today()

        def expected_day(year, month):
            max_day = calendar.monthrange(year, month)[1]
            return min(today.day, max_day)

        result = parse_partial_date(year=2026, month="Feb")
        self.assertEqual(result, date(2026, 2, expected_day(2026, 2)))

        result = parse_partial_date(year=2026, month="Mar")
        self.assertEqual(result, date(2026, 3, expected_day(2026, 3)))

    def test_full_date_uses_every_component(self):
        result = parse_partial_date(year=2026, month="Feb", day="15th")
        self.assertEqual(result, date(2026, 2, 15))

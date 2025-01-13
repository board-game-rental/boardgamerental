from datetime import date

from django.test import TestCase

from .views import get_next_monday


class NextMondayTestCase(TestCase):
    def test_get_next_monday(self):

        test_date = date(2023, 7, 8)
        next_monday = get_next_monday(test_date)
        self.assertEqual(next_monday.weekday(), 0)
        self.assertLessEqual((next_monday - test_date).days, 7)

        test_date = date(2023, 12, 15)
        next_monday = get_next_monday(test_date)
        self.assertEqual(next_monday.weekday(), 0)
        self.assertLessEqual((next_monday - test_date).days, 7)

        test_date = date(2025, 9, 22)
        next_monday = get_next_monday(test_date)
        self.assertEqual(next_monday.weekday(), 0)
        self.assertLessEqual((next_monday - test_date).days, 7)

        test_date = date(2023, 9, 26)
        next_monday = get_next_monday(test_date)
        self.assertEqual(next_monday.weekday(), 0)
        self.assertLessEqual((next_monday - test_date).days, 7)

        test_date = date(2024, 7, 11)
        next_monday = get_next_monday(test_date)
        self.assertEqual(next_monday.weekday(), 0)
        self.assertLessEqual((next_monday - test_date).days, 7)

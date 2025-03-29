import unittest
from datetime import datetime
from src.utils.helpers import (
    format_problem_message,
    validate_rating,
    chunks,
    parse_datetime,
    extract_problem_id
)
from tests.test_data import SAMPLE_DB_PROBLEM


class TestUtils(unittest.TestCase):
    def test_format_problem_message(self):
        result = format_problem_message(SAMPLE_DB_PROBLEM)
        self.assertIn('Test Problem', result)
        self.assertIn('800', result)
        self.assertIn('math', result)

    def test_validate_rating_valid(self):
        self.assertEqual(validate_rating('800'), 800)
        self.assertEqual(validate_rating('1500'), 1500)

    def test_validate_rating_invalid(self):
        self.assertIsNone(validate_rating('850'))
        self.assertIsNone(validate_rating('text'))
        self.assertIsNone(validate_rating('3501'))

    def test_chunks(self):
        result = list(chunks([1, 2, 3, 4, 5], 2))
        self.assertEqual(result, [[1, 2], [3, 4], [5]])

    def test_parse_datetime(self):
        dt = parse_datetime('1672531200')  # 2023-01-01 00:00:00
        self.assertEqual(dt.year, 2023)
        self.assertIsNone(parse_datetime('invalid'))

    def test_extract_problem_id(self):
        url = 'https://codeforces.com/problemset/problem/1/A'
        result = extract_problem_id(url)
        self.assertEqual(result, (1, 'A'))
        self.assertIsNone(extract_problem_id('invalid_url'))

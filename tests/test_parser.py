import unittest
from unittest.mock import patch, MagicMock
from src.parser.codeforces_api import (
    CodeforcesAPIError,
    fetch_problems,
    process_problems,
    parse_and_save_problems
)
from tests.test_data import SAMPLE_PROBLEMS, SAMPLE_STATISTICS


class TestCodeforcesAPI(unittest.TestCase):
    @patch('requests.get')
    def test_fetch_problems_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': SAMPLE_PROBLEMS,
                'problemStatistics': SAMPLE_STATISTICS
            }
        }
        mock_get.return_value = mock_response

        problems, stats = fetch_problems()
        self.assertEqual(len(problems), 2)
        self.assertEqual(len(stats), 2)

    @patch('requests.get')
    def test_fetch_problems_failure(self, mock_get):
        mock_get.side_effect = Exception("API Error")

        try:
            fetch_problems()
            self.fail("Expected CodeforcesAPIError to be raised")
        except CodeforcesAPIError as e:
            self.assertIn("Failed after 3 attempts", str(e))

    def test_process_problems(self):
        processed = process_problems(SAMPLE_PROBLEMS, SAMPLE_STATISTICS)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]['name'], 'Test Problem')
        self.assertEqual(processed[1]['solved_count'], 200)

    @patch('src.parser.codeforces_api.save_problems_to_db')
    @patch('src.parser.codeforces_api.fetch_problems')
    def test_parse_and_save_problems(self, mock_fetch, mock_save):
        mock_fetch.return_value = (SAMPLE_PROBLEMS, SAMPLE_STATISTICS)
        parse_and_save_problems()
        mock_save.assert_called_once()
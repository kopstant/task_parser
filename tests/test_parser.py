import unittest
from unittest.mock import patch, MagicMock
from src.parser.codeforces_api import (
    CodeforcesAPIError,
    fetch_problems,
    process_problems,
    parse_and_save_problems,
    MAX_RETRIES,
    SessionLocal
)
from tests.test_data import SAMPLE_PROBLEMS, SAMPLE_STATISTICS


class TestCodeforcesAPI(unittest.TestCase):
    @patch('requests.Session')
    def test_fetch_problems_success(self, mock_session):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'OK',
            'result': {
                'problems': SAMPLE_PROBLEMS,
                'problemStatistics': SAMPLE_STATISTICS
            }
        }
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        problems, stats = fetch_problems()
        self.assertEqual(len(problems), len(SAMPLE_PROBLEMS))
        self.assertEqual(len(stats), len(SAMPLE_STATISTICS))
        self.assertEqual(problems[0]['name'], 'Test Problem')

    @patch('requests.Session')
    def test_fetch_problems_failure(self, mock_session):
        mock_session.return_value.get.side_effect = Exception("API Error")

        with self.assertRaises(CodeforcesAPIError) as context:
            fetch_problems()
        self.assertIn("API request failed", str(context.exception))

    def test_process_problems(self):
        processed = process_problems(SAMPLE_PROBLEMS, SAMPLE_STATISTICS)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]['name'], 'Test Problem')
        self.assertEqual(processed[0]['solved_count'], 100)
        self.assertEqual(processed[1]['solved_count'], 200)
        self.assertEqual(processed[0]['tags'], ['math'])
        self.assertEqual(processed[1]['tags'], ['dp'])

    @patch('src.parser.codeforces_api.fetch_problems')
    @patch('src.parser.codeforces_api.create_problems_batch')
    def test_parse_and_save_problems(self, mock_create_batch, mock_fetch):
        mock_fetch.return_value = (SAMPLE_PROBLEMS, SAMPLE_STATISTICS)
        
        # Мокаем сессию базы данных
        mock_session = MagicMock()
        mock_session.execute().scalar.return_value = 0
        
        with patch('src.parser.codeforces_api.SessionLocal') as mock_session_class:
            mock_session_class.return_value = mock_session
            result = parse_and_save_problems()
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['count'], len(SAMPLE_PROBLEMS))
            mock_create_batch.assert_called_once()
            mock_session.close.assert_called()
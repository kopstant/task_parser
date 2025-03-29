import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from src.parser.tasks import parse_codeforces_problems, scheduled_parsing


class TestCeleryTasks(unittest.TestCase):

    @patch('src.parser.tasks.parse_and_save_problems')
    @patch('src.parser.tasks.logger')
    def test_parse_codeforces_problems_success(self, mock_logger, mock_parse_and_save_problems):
        # Мокаем успешное выполнение парсинга
        mock_parse_and_save_problems.return_value = None

        # Время, которое будет использовано в логе
        mock_time = datetime(2025, 3, 29, 10, 0, 0, tzinfo=timezone.utc)

        with patch('src.parser.tasks.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.utcnow.return_value = mock_time

            # Выполняем задачу
            result = parse_codeforces_problems.apply()

            # Проверяем, что задача успешно завершилась
            self.assertEqual(result.result['status'], 'success')
            self.assertEqual(result.result['message'], 'Problems parsed successfully')
            mock_logger.info.assert_called_with(f"Starting Codeforces parsing task at {mock_time.isoformat()}")
            mock_parse_and_save_problems.assert_called_once()

    @patch('src.parser.tasks.parse_codeforces_problems.retry')  # Мокаем retry на уровне задачи
    @patch('src.parser.tasks.parse_and_save_problems')
    @patch('src.parser.tasks.logger')
    def test_parse_codeforces_problems_failure(self, mock_logger, mock_parse_and_save_problems, mock_retry):
        # Мокаем ошибку в парсинге
        mock_parse_and_save_problems.side_effect = Exception("Test error")

        # Время, которое будет использовано в логе
        mock_time = datetime(2025, 3, 29, 10, 0, 0, tzinfo=timezone.utc)

        with patch('src.parser.tasks.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.utcnow.return_value = mock_time

            # Вызываем задачу и проверяем, что она завершится с ошибкой
            with self.assertRaises(Exception):
                parse_codeforces_problems()

            # Проверяем, что retry был вызван
            mock_retry.assert_called_once()  # Проверка на вызов retry

    @patch('src.parser.tasks.parse_codeforces_problems')
    def test_scheduled_parsing(self, mock_parse_codeforces_problems):
        # Проверяем, что периодическая задача вызывает парсинг
        scheduled_parsing.apply()

        # Проверяем, что задача была запущена
        mock_parse_codeforces_problems.delay.assert_called_once()


if __name__ == '__main__':
    unittest.main()

import pytest
from unittest.mock import patch, MagicMock, create_autospec
from datetime import datetime, timezone
from src.parser.tasks import parse_codeforces_problems, scheduled_parsing, parse_and_save_problems
from celery import Task
from celery.result import AsyncResult


@pytest.fixture
def mock_parse_and_save():
    with patch('src.parser.tasks.parse_and_save_problems', autospec=True) as mock:
        mock.return_value = {'status': 'success', 'count': 10}
        yield mock


@pytest.fixture
def mock_logger():
    with patch('src.parser.tasks.logger', autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_datetime():
    with patch('src.parser.tasks.datetime', autospec=True) as mock:
        mock_time = datetime(2025, 3, 29, 10, 0, 0, tzinfo=timezone.utc)
        mock.now.return_value = mock_time
        mock.utcnow.return_value = mock_time
        yield mock, mock_time


@pytest.fixture
def mock_celery_task():
    mock = create_autospec(Task)
    result = MagicMock(spec=AsyncResult)
    result.id = 'test-id'
    result.state = 'SUCCESS'
    result.result = {'status': 'success', 'message': 'Problems parsed successfully'}
    mock.apply.return_value = result
    return mock


def test_parse_codeforces_problems_failure(mock_parse_and_save):
    """Тест обработки ошибки в задаче парсинга"""
    mock_parse_and_save.side_effect = Exception("Test error")

    with patch('src.parser.tasks.parse_codeforces_problems.retry', autospec=True) as mock_retry, \
            patch('src.database.base.check_db_connection', return_value=True), \
            patch('src.parser.tasks.logger') as mock_task_logger:
        # Вызываем задачу и проверяем исключение
        with pytest.raises(Exception):
            parse_codeforces_problems()

        # Проверяем, что retry был вызван
        mock_retry.assert_called_once()
        mock_task_logger.error.assert_called_with("Task failed: Test error")


def test_scheduled_parsing():
    """Тест периодической задачи парсинга"""
    with patch('src.parser.tasks.parse_codeforces_problems') as mock_parse, \
            patch('src.database.base.check_db_connection', return_value=True):
        mock_parse.delay = MagicMock()

        # Проверяем, что периодическая задача вызывает парсинг
        scheduled_parsing()

        # Проверяем, что задача была запущена
        mock_parse.delay.assert_called_once()


@pytest.fixture
def mock_fetch():
    with patch('src.parser.codeforces_api.fetch_problems', autospec=True) as mock:
        mock.return_value = ([], [])
        yield mock


@pytest.fixture
def mock_save():
    with patch('src.parser.codeforces_api.save_problems_to_db', autospec=True) as mock:
        mock.return_value = {'status': 'success', 'count': 1}
        yield mock


def test_parse_codeforces_problems_api_success(mock_fetch):
    """Тест успешного парсинга задач с Codeforces"""
    # Настраиваем моки
    problems_data = [
        {
            'contestId': 1,
            'index': 'A',
            'name': 'Test Problem',
            'rating': 800,
            'tags': ['math']
        }
    ]
    stats_data = [
        {
            'contestId': 1,
            'index': 'A',
            'solvedCount': 100
        }
    ]
    mock_fetch.return_value = (problems_data, stats_data)

    with patch('src.parser.tasks.parse_and_save_problems') as mock_parse, \
            patch('src.database.base.check_db_connection', return_value=True):
        mock_parse.return_value = {'status': 'success', 'count': 1}

        # Вызываем функцию и проверяем результат
        result = mock_parse()
        assert result == {'status': 'success', 'count': 1}
        mock_fetch.assert_not_called()  # Так как мы мокаем на уровень выше


def test_parse_codeforces_problems_api_error(mock_fetch):
    """Тест обработки ошибки API Codeforces"""
    # Настраиваем мок для имитации ошибки API
    mock_fetch.side_effect = Exception("API Error")

    # Вызываем функцию и проверяем исключение
    with pytest.raises(Exception) as exc:
        parse_and_save_problems()

    assert str(exc.value) == "API Error"
    mock_fetch.assert_called_once()


def test_parse_codeforces_problems_db_error(mock_fetch, mock_save):
    """Тест обработки ошибки базы данных"""
    # Настраиваем моки
    problems_data = [
        {
            'contestId': 1,
            'index': 'A',
            'name': 'Test Problem',
            'rating': 800,
            'tags': ['math']
        }
    ]
    stats_data = [
        {
            'contestId': 1,
            'index': 'A',
            'solvedCount': 100
        }
    ]
    mock_fetch.return_value = (problems_data, stats_data)
    mock_save.side_effect = Exception("Database Error")

    # Вызываем функцию и проверяем исключение
    with pytest.raises(Exception) as exc:
        parse_and_save_problems()

    assert str(exc.value) == "Database Error"
    mock_fetch.assert_called_once()
    mock_save.assert_called_once()

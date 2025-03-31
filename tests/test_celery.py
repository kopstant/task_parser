import pytest
from unittest.mock import patch, MagicMock, create_autospec
from celery import Celery
from src.celery.celery_app import app
from src.celery.tasks import parse_codeforces


# Тестовые данные
SAMPLE_TASK_CONFIG = {
    'parse-codeforces-hourly': {
        'task': 'src.celery.tasks.parse_codeforces',
        'schedule': 3600,
        'options': {
            'queue': 'parsing',
            'expires': 3500
        }
    }
}


@pytest.fixture
def mock_celery():
    mock = create_autospec(Celery)
    mock.conf = MagicMock()
    mock.conf.broker_url = "redis://redis:6379/0"
    mock.conf.result_backend = "redis://redis:6379/0"
    mock.conf.beat_schedule = SAMPLE_TASK_CONFIG
    return mock


@pytest.fixture
def mock_sender():
    mock = MagicMock()
    mock.app = MagicMock()
    mock.app.amqp = MagicMock()
    mock.app.amqp.default_queue = MagicMock()
    mock.app.amqp.default_queue.name = 'parsing'
    return mock


@pytest.fixture
def mock_parse():
    with patch('src.celery.tasks.parse_codeforces', autospec=True) as mock:
        mock.delay = MagicMock()
        yield mock


@pytest.fixture
def mock_logger():
    with patch('src.celery.celery_app.logger', autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_db_check():
    with patch('src.database.base.check_db_connection', autospec=True) as mock:
        mock.return_value = True
        yield mock


def test_celery_config(mock_celery):
    """Тест конфигурации Celery"""
    with patch('src.celery.celery_app.app', mock_celery):
        # Проверяем основные настройки
        assert app.conf.broker_url == "redis://redis:6379/0"
        assert app.conf.result_backend == "redis://redis:6379/0"
        assert isinstance(app.conf.beat_schedule, dict)


def test_parse_codeforces_task_error(mock_db_check):
    """Тест обработки ошибок в задаче парсинга"""
    with patch('src.celery.tasks.parse_and_save_problems') as mock_parse:
        mock_parse.side_effect = Exception("Test error")

        # Проверяем, что исключение обрабатывается
        with pytest.raises(Exception):
            parse_codeforces()

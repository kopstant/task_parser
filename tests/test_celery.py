import pytest
from unittest.mock import patch, MagicMock, create_autospec
from celery import Celery
from celery.signals import worker_ready, beat_init
from src.celery.celery_app import app, at_start, on_beat_init, init_celery
from src.celery.tasks import parse_codeforces
from src.database.crud import check_db_connection
from datetime import datetime, timezone

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

def test_worker_ready_handler(mock_sender):
    """Тест обработчика готовности воркера для очереди parsing"""
    with patch('src.celery.tasks.parse_codeforces') as mock_task, \
         patch('src.database.base.check_db_connection', return_value=True), \
         patch('src.celery.celery_app.logger') as mock_logger:
        mock_task.delay = MagicMock()
        
        # Вызываем обработчик
        init_celery(mock_sender)
        
        # Проверяем, что задача была запущена
        mock_task.delay.assert_called_once()
        mock_logger.info.assert_any_call("Starting initial parsing task")

def test_worker_ready_handler_wrong_queue(mock_sender):
    """Тест обработчика готовности воркера для другой очереди"""
    mock_sender.app.amqp.default_queue.name = 'other'
    
    with patch('src.celery.tasks.parse_codeforces') as mock_task, \
         patch('src.database.base.check_db_connection', return_value=True), \
         patch('src.celery.celery_app.logger') as mock_logger:
        mock_task.delay = MagicMock()
        
        # Вызываем обработчик
        init_celery(mock_sender)
        
        # Проверяем, что задача не была запущена
        mock_task.delay.assert_not_called()
        mock_logger.info.assert_any_call("Worker does not handle parsing queue, skipping initial parse")

def test_beat_init_handler(mock_sender):
    """Тест обработчика инициализации beat"""
    mock_sender.app.conf.beat_schedule = SAMPLE_TASK_CONFIG
    
    with patch('src.celery.celery_app.logger') as mock_logger:
        # Вызываем обработчик
        on_beat_init(mock_sender)
        
        # Проверяем логирование
        assert mock_logger.info.call_count >= 2
        mock_logger.info.assert_any_call("Celery beat started. Scheduled tasks:")

def test_parse_codeforces_task():
    """Тест задачи парсинга Codeforces"""
    with patch('src.celery.tasks.parse_and_save_problems') as mock_parse, \
         patch('src.database.base.check_db_connection', return_value=True), \
         patch('src.celery.tasks.logger') as mock_logger, \
         patch('src.celery.tasks.datetime') as mock_datetime:
        mock_parse.return_value = {'status': 'success', 'count': 10}
        mock_time = datetime(2025, 3, 29, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_time
        
        # Вызываем задачу
        result = parse_codeforces()
        
        # Проверяем результат
        assert result == {'status': 'success', 'count': 10}
        mock_parse.assert_called_once()
        mock_logger.info.assert_any_call("Database connection check passed, starting parsing")
        mock_logger.info.assert_any_call(f"Starting scheduled parsing task at {mock_time.strftime('%Y-%m-%d %H:%M:%S')}")
        mock_logger.info.assert_any_call("Parsing completed successfully: {'status': 'success', 'count': 10}")

def test_parse_codeforces_task_error(mock_db_check):
    """Тест обработки ошибок в задаче парсинга"""
    with patch('src.celery.tasks.parse_and_save_problems') as mock_parse:
        mock_parse.side_effect = Exception("Test error")
        
        # Проверяем, что исключение обрабатывается
        with pytest.raises(Exception):
            parse_codeforces() 
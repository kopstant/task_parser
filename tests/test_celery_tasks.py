import pytest
from unittest.mock import patch, MagicMock
from src.celery.tasks import parse_codeforces
from src.parser.codeforces_api import parse_and_save_problems


@pytest.fixture
def mock_fetch_problems():
    with patch('src.parser.codeforces_api.fetch_problems') as mock:
        yield mock


@pytest.fixture
def mock_process_problems():
    with patch('src.parser.codeforces_api.process_problems') as mock:
        yield mock


@pytest.fixture
def mock_create_problems_batch():
    with patch('src.database.crud.create_problems_batch') as mock:
        yield mock


@pytest.fixture
def mock_check_db_connection():
    with patch('src.database.base.check_db_connection') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_session():
    return MagicMock()


def test_parse_codeforces_error(mock_fetch_problems, mock_check_db_connection):
    """Тест обработки ошибок при парсинге"""
    mock_fetch_problems.side_effect = Exception("API Error")

    # Проверяем, что функция обрабатывает ошибку
    with pytest.raises(Exception):
        parse_codeforces()


def test_parse_codeforces_db_error(mock_check_db_connection):
    """Тест ошибки подключения к БД"""
    mock_check_db_connection.return_value = False

    # Проверяем, что функция обрабатывает ошибку
    with pytest.raises(Exception) as exc_info:
        parse_codeforces()
    assert str(exc_info.value) == "Database connection failed"


def test_parse_and_save_problems_error(mock_fetch_problems):
    """Тест обработки ошибок при парсинге и сохранении"""
    mock_fetch_problems.side_effect = Exception("API Error")

    # Проверяем, что функция обрабатывает ошибку
    with pytest.raises(Exception):
        parse_and_save_problems()

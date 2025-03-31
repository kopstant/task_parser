import pytest
from unittest.mock import MagicMock, patch
from src.database.init_db import check_db_connection


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_session():
    return MagicMock()


def test_check_db_connection_failure(mock_engine):
    """Тест неудачного подключения к базе данных"""
    with patch('src.database.base.engine', mock_engine):
        mock_engine.connect.side_effect = Exception("Connection error")

        result = check_db_connection()

        assert result is False

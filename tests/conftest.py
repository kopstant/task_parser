import os
import pytest
from telegram.ext import Application
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from unittest.mock import patch, MagicMock, AsyncMock

os.environ['TESTING'] = 'True'


@pytest.fixture
async def app():
    return Application.builder().token("TEST_TOKEN").build()


@pytest.fixture(scope='session')
def db_engine():
    # Используем SQLite в памяти для тестов
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Фикстуры для мока обработчиков
@pytest.fixture(autouse=True)
def mock_redis():
    """Мок для Redis"""
    with patch('redis.Redis') as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture(autouse=True)
def test_env():
    """Установка переменных окружения для тестов"""
    os.environ['TESTING'] = 'True'
    yield
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


@pytest.fixture
def mock_db():
    """Мок для базы данных"""
    with patch('src.database.base.engine') as mock:
        yield mock


@pytest.fixture
def mock_session():
    """Мок для сессии базы данных"""
    with patch('src.database.base.SessionLocal') as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_handlers():
    """Моки для обработчиков"""
    with patch('src.bot.handlers.start_command') as start_mock, \
         patch('src.bot.handlers.help_command') as help_mock, \
         patch('src.bot.handlers.get_random_problem') as random_mock, \
         patch('src.bot.handlers.get_problem_by_rating') as rating_mock:
        
        start_mock.return_value = AsyncMock()
        help_mock.return_value = AsyncMock()
        random_mock.return_value = AsyncMock()
        rating_mock.return_value = AsyncMock()
        
        yield {
            'start': start_mock,
            'help': help_mock,
            'random': random_mock,
            'rating': rating_mock
        }

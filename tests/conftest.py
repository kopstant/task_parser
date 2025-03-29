import os

import pytest
from telegram.ext import Application
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.config import config

os.environ['TESTING'] = 'True'


@pytest.fixture
async def app():
    return Application.builder().token("TEST_TOKEN").build()


@pytest.fixture(scope='session')
def db_engine():
    # Используем TEST_DATABASE_URL из конфига
    engine = create_engine(config.TEST_DATABASE_URL)
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

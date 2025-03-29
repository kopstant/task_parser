from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from src.config import config
import os

# Конфигурация движка
engine_args = {
    'pool_pre_ping': True,
    'echo': False
}

# Используем TEST_DATABASE_URL если в режиме тестирования
DB_URL = config.TEST_DATABASE_URL if config.TESTING else config.DATABASE_URL

# Особые настройки для SQLite
if 'sqlite' in DB_URL:
    engine_args.update({
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool
    })

engine = create_engine(DB_URL, **engine_args)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация БД (создание таблиц)"""
    Base.metadata.create_all(bind=engine)

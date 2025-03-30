from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import config
from sqlalchemy import text

# Конфигурация движка
engine_args = {
    'pool_pre_ping': True,
    'echo': False
}

DB_URL = config.DATABASE_URL

engine = create_engine(DB_URL, **engine_args)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


def check_db_connection():
    """Новая функция для проверки подключения"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("Database connection: OK")
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация БД (создание таблиц)"""
    Base.metadata.create_all(bind=engine)

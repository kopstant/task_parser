import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    TESTING = os.getenv('TESTING', 'False') == 'True'

    # Telegram
    @property
    def TELEGRAM_TOKEN(self):
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_TOKEN должен быть установлен в файле .env")
        return token

    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    if not POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD must be set in .env file")
    POSTGRES_DB = os.getenv('POSTGRES_NAME', 'codeforce_parser')

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Основная база данных
    @property
    def DATABASE_URL(self):
        if url := os.getenv('DATABASE_URL'):
            return url
        password = self.POSTGRES_PASSWORD
        return f"postgresql://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Тестовая база данных
    @property
    def TEST_DATABASE_URL(self):
        if url := os.getenv('TEST_DATABASE_URL'):
            return url
        password = self.POSTGRES_PASSWORD
        return f"postgresql://{self.POSTGRES_USER}:{password}@localhost:5432/{self.POSTGRES_DB}_test"


config = Config()

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN

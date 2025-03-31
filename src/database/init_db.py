from src.database.base import init_db, engine
from src.parser.codeforces_api import parse_and_save_problems
import logging
import signal
from contextlib import contextmanager
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


@contextmanager
def timeout(time):
    def signal_handler(signum, frame):
        raise TimeoutException()

    # Register a function to raise a TimeoutException on the signal
    signal.signal(signal.SIGALRM, signal_handler)

    try:
        signal.alarm(time)  # Trigger alarm in `time` seconds
        yield
    finally:
        signal.alarm(0)  # Disable the alarm


def check_db_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        connection = engine.connect()
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False


def main():
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")

        logger.info("Starting initial parsing...")
        with timeout(300):  # 5 минут таймаут
            result = parse_and_save_problems()
            logger.info(f"Initial parsing completed: {result}")
            sys.exit(0)  # Успешное завершение
    except TimeoutException:
        logger.error("Parsing timeout after 5 minutes")
        sys.exit(1)  # Выход с ошибкой
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        sys.exit(1)  # Выход с ошибкой


if __name__ == "__main__":
    main()

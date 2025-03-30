from .celery_app import app
from src.parser.codeforces_api import parse_and_save_problems
from src.database.base import check_db_connection
import logging
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from datetime import datetime

logger = get_task_logger(__name__)

@app.task(
    name='parse_codeforces',
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 минута между повторами
    autoretry_for=(Exception,),
    retry_backoff=True,  # Экспоненциальная задержка между повторами
)
def parse_codeforces(self):
    """
    Celery задача для парсинга задач с Codeforces.
    Включает проверку подключения к БД и автоматические повторы при ошибках.
    """
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Starting scheduled parsing task at {current_time}")
        
        # Проверяем подключение к БД перед парсингом
        if not check_db_connection():
            logger.error("Database connection check failed")
            raise Exception("Database connection failed")

        logger.info("Database connection check passed, starting parsing")
        result = parse_and_save_problems()
        logger.info(f"Parsing completed successfully: {result}")
        
        # Логируем следующий запланированный запуск
        next_hour = (datetime.now().replace(minute=0, second=0, microsecond=0)
                    .timestamp() + 3600)
        next_run = datetime.fromtimestamp(next_hour).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Next scheduled run at: {next_run}")
        
        return result

    except MaxRetriesExceededError as e:
        logger.error(f"Task failed after maximum retries: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise self.retry(exc=e)

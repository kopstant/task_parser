from celery import shared_task
from datetime import datetime, timezone
import logging
from src.parser.codeforces_api import parse_and_save_problems

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(bind=True, name='parse_codeforces_problems')
def parse_codeforces_problems(self):
    """
    Celery задача для парсинга задач с Codeforces
    """
    logger.info(f"Starting Codeforces parsing task at {datetime.now(timezone.utc).isoformat()}")
    try:
        parse_and_save_problems()
        return {
            'status': 'success',
            'message': 'Problems parsed successfully',
            'time': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise self.retry(exc=e, countdown=60)  # Повтор через 60 секунд при ошибке


# Периодическая задача (для Celery Beat)
@shared_task(name='scheduled_parsing')
def scheduled_parsing():
    """
    Запланированный парсинг (вызывается каждый час)
    """
    return parse_codeforces_problems.delay()

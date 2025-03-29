from celery_config.celery_app import app
from src.parser.codeforces_api import parse_and_save_problems
from src.database.base import SessionLocal
from src.database.models import Problem
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True, name='parse_codeforces_problems', queue='parsing')
def parse_codeforces_problems(self):
    """Фоновая задача для парсинга задач с Codeforces"""
    try:
        logger.info("Starting Codeforces parsing task")

        # Основная логика парсинга
        parse_and_save_problems()

        # Проверка результатов
        db = SessionLocal()
        count = db.query(Problem).count()
        db.close()

        logger.info(f"Successfully parsed. Total problems in DB: {count}")
        return {
            "status": "success",
            "problems_count": count,
            "message": "Problems parsed successfully"
        }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=300)  # Повтор через 5 минут

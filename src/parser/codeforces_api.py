import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Tuple
from datetime import datetime, UTC
import logging
import time
from src.database.base import SessionLocal
from src.database.crud import create_problems_batch
from sqlalchemy import text, exc

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://codeforces.com/api"
MAX_RETRIES = 3
TIMEOUT = 10
RATE_LIMIT_WAIT = 5  # секунды ожидания при 429
BATCH_SIZE = 100  # Размер пакета для сохранения в БД


class CodeforcesAPIError(Exception):
    """Кастомное исключение для ошибок API Codeforces"""
    pass


def requests_retry_session():
    """Создает сессию requests с автоматическими повторами"""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def fetch_problems() -> Tuple[List[Dict], List[Dict]]:
    """Получение задач и статистики с Codeforces API"""
    endpoint = f"{BASE_URL}/problemset.problems"
    session = requests_retry_session()

    try:
        response = session.get(endpoint, timeout=TIMEOUT)

        # Обработка ограничения запросов
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded. Waiting {RATE_LIMIT_WAIT} seconds...")
            time.sleep(RATE_LIMIT_WAIT)
            return fetch_problems()  # Рекурсивный вызов после ожидания

        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            error_msg = f"API returned status: {data['status']}"
            if 'comment' in data:
                error_msg += f", comment: {data['comment']}"
            raise CodeforcesAPIError(error_msg)

        return data['result']['problems'], data['result']['problemStatistics']

    except Exception as e:
        logger.error(f"Failed to fetch problems after {MAX_RETRIES} attempts: {str(e)}")
        raise CodeforcesAPIError(f"API request failed: {str(e)}")


def process_problems(problems: List[Dict], problem_stats: List[Dict]) -> List[Dict]:
    """
    Обработка сырых данных задач с объединением статистики
    """
    processed = []
    stats_map = {(p['contestId'], p['index']): p for p in problem_stats}

    for problem in problems:
        key = (problem['contestId'], problem['index'])
        stat = stats_map.get(key, {})

        processed.append({
            'contest_id': problem['contestId'],
            'index': problem['index'],
            'name': problem['name'],
            'rating': problem.get('rating'),
            'solved_count': stat.get('solvedCount', 0),
            'tags': problem.get('tags', [])
        })

    return processed


def save_problems_to_db(problems: List[Dict]) -> None:
    """
    Сохранение задач в базу данных пакетами
    """
    db = SessionLocal()
    try:
        total_problems = len(problems)
        logger.info(f"Starting to save {total_problems} problems in batches of {BATCH_SIZE}")

        # Разбиваем задачи на пакеты
        for i in range(0, total_problems, BATCH_SIZE):
            batch = problems[i:i + BATCH_SIZE]
            logger.info(f"Processing batch {i//BATCH_SIZE + 1} of {(total_problems + BATCH_SIZE - 1)//BATCH_SIZE}")
            
            try:
                create_problems_batch(db, batch)
                logger.info(f"Batch {i//BATCH_SIZE + 1} saved successfully")
            except Exception as e:
                logger.error(f"Error saving batch: {str(e)}")
                db.rollback()
                continue

    finally:
        db.close()


def parse_and_save_problems() -> Dict[str, any]:
    try:
        logger.info("=== Начало парсинга ===")
        problems, stats = fetch_problems()
        processed = process_problems(problems, stats)

        logger.info(f"Получено задач: {len(processed)}")
        save_problems_to_db(processed)

        db = SessionLocal()
        try:
            topics_count = db.execute(text("SELECT COUNT(*) FROM topics")).scalar()
            logger.info(f"Тем в БД после сохранения: {topics_count}")
        finally:
            db.close()

        return {"status": "success", "count": len(processed)}
    except Exception as e:
        logger.error(f"!!! Ошибка парсинга: {str(e)}")
        raise

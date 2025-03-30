import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Tuple
from datetime import datetime, UTC
import logging
import time
from src.database.base import SessionLocal
from src.database.crud import create_problem
from sqlalchemy import text, exc

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://codeforces.com/api"
MAX_RETRIES = 3
TIMEOUT = 10
RATE_LIMIT_WAIT = 5  # секунды ожидания при 429


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
    db = SessionLocal()
    try:
        for problem_data in problems:
            try:
                # Добавим логирование перед сохранением
                print(f"Processing: {problem_data['contest_id']}{problem_data['index']} - {problem_data['name']}")

                create_problem(
                    db,
                    contest_id=problem_data['contest_id'],
                    index=problem_data['index'],
                    name=problem_data['name'],
                    rating=problem_data.get('rating'),
                    solved_count=problem_data['solved_count'],
                    tags=problem_data['tags']
                )
                db.commit()  # Фиксируем после каждой задачи
            except Exception as e:
                db.rollback()
                print(f"Error saving problem {problem_data['contest_id']}{problem_data['index']}: {str(e)}")
                continue
    finally:
        db.close()


def parse_and_save_problems() -> Dict[str, any]:
    """
    Основная функция парсинга и сохранения задач с возвратом статистики
    """
    logger.info(f"Starting parsing at {datetime.now(UTC).isoformat()}")
    try:
        problems, problem_stats = fetch_problems()
        processed_problems = process_problems(problems, problem_stats)
        save_problems_to_db(processed_problems)

        result = {
            'status': 'success',
            'total_problems': len(processed_problems),
            'timestamp': datetime.now(UTC).isoformat()
        }
        logger.info(f"Parsing completed: {result}")
        return result

    except Exception as e:
        error_msg = f"Parsing failed: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg,
            'timestamp': datetime.now(UTC).isoformat()
        }

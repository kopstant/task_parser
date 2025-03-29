import requests
from typing import List, Dict, Tuple
from datetime import datetime, UTC
import logging
from src.database.base import SessionLocal
from src.database.models import Problem, Topic
from src.database.crud import get_or_create_topic, create_problem

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://codeforces.com/api"
MAX_RETRIES = 3
TIMEOUT = 10


class CodeforcesAPIError(Exception):
    """Кастомное исключение для ошибок API Codeforces"""
    pass


def fetch_problems() -> Tuple[List[Dict], List[Dict]]:
    endpoint = f"{BASE_URL}/problemset.problems"

    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(endpoint, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                raise CodeforcesAPIError(f"API returned status: {data['status']}")

            return data['result']['problems'], data['result']['problemStatistics']

        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

    raise CodeforcesAPIError(f"Failed after {MAX_RETRIES} attempts: {str(last_exception)}")


def process_problems(problems: List[Dict], problem_stats: List[Dict]) -> List[Dict]:
    """
    Обрабатывает сырые данные задач, объединяя с их статистикой
    Возвращает список обработанных задач
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
    Сохраняет задачи в базу данных
    """
    db = SessionLocal()
    try:
        for problem_data in problems:
            # Проверяем, существует ли уже задача
            existing = db.query(Problem).filter(
                Problem.contest_id == problem_data['contest_id'],
                Problem.index == problem_data['index']
            ).first()

            if not existing:
                # Создаем новую задачу
                create_problem(
                    db,
                    contest_id=problem_data['contest_id'],
                    index=problem_data['index'],
                    name=problem_data['name'],
                    rating=problem_data.get('rating'),
                    solved_count=problem_data['solved_count'],
                    tags=problem_data['tags']
                )
                logger.info(f"Added problem: {problem_data['contest_id']}{problem_data['index']}")
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving problems: {str(e)}")
        raise
    finally:
        db.close()


def parse_and_save_problems() -> None:
    """
    Основная функция парсинга и сохранения задач
    """
    logger.info(f"Starting parsing at {datetime.now(UTC).isoformat()}")
    try:
        problems, problem_stats = fetch_problems()
        processed_problems = process_problems(problems, problem_stats)
        save_problems_to_db(processed_problems)
        logger.info(f"Successfully parsed {len(processed_problems)} problems")
    except Exception as e:
        logger.error(f"Parsing failed: {str(e)}")
        raise
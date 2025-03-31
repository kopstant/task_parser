from typing import List, Any, Optional
from datetime import datetime
import logging
import re

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_problem_message(problem: Any) -> str:
    """
    Форматирует информацию о задаче для вывода в Telegram

    Args:
        problem: Объект задачи из БД

    Returns:
        str: Отформатированное сообщение
    """
    try:
        topics = ', '.join(topic.name for topic in problem.topics) if problem.topics else 'нет тегов'
        problem_url = f"https://codeforces.com/problemset/problem/{problem.contest_id}/{problem.index}"

        return (
            f"<b>{problem.name}</b>\n"
            f"<b>Сложность:</b> {problem.rating if problem.rating else 'не указана'}\n"
            f"<b>Темы:</b> {topics}\n"
            f"<b>Решений:</b> {problem.solved_count}\n"
            f"<b>Ссылка:</b> {problem_url}"
        )
    except Exception as e:
        logger.error(f"Error formatting problem message: {str(e)}")
        return "Не удалось сформировать информацию о задаче"


def validate_rating(rating: str) -> Optional[int]:
    """
    Проверяет валидность введенного рейтинга задачи

    Args:
        rating: Введенная пользователем строка

    Returns:
        Optional[int]: Числовой рейтинг или None если невалидный
    """
    try:
        rating_num = int(rating)
        if 800 <= rating_num <= 3500 and rating_num % 100 == 0:
            return rating_num
        return None
    except (ValueError, TypeError):
        return None


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Разбивает список на подсписки заданного размера

    Args:
        lst: Исходный список
        n: Размер чанка

    Returns:
        List[List[Any]]: Список чанков
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Парсит строку даты-времени из API Codeforces

    Args:
        dt_str: Строка даты-времени (Unix timestamp)

    Returns:
        Optional[datetime]: Объект datetime или None при ошибке
    """
    try:
        return datetime.fromtimestamp(int(dt_str))
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse datetime: {dt_str}")
        return None


def extract_problem_id(url: str) -> Optional[tuple]:
    """
    Извлекает contest_id и index из URL задачи Codeforces

    Args:
        url: URL задачи

    Returns:
        Optional[tuple]: (contest_id, index) или None
    """
    pattern = r'problemset/problem/(\d+)/(\w+)'
    match = re.search(pattern, url)
    if match:
        return int(match.group(1)), match.group(2)
    return None

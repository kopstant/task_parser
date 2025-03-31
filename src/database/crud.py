from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict
from src.database.models import Problem, Topic
from sqlalchemy import text
import logging
from src.database.base import engine

logger = logging.getLogger(__name__)


def check_db_connection() -> bool:
    """Проверить подключение к базе данных"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def get_topic_by_name(db: Session, name: str) -> Optional[Topic]:
    """Получить тему по имени"""
    return db.query(Topic).filter(Topic.name == name).first()


def create_topic(db: Session, name: str) -> Topic:
    """Создать новую тему"""
    topic = Topic(name=name)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def get_or_create_topic(db: Session, name: str) -> Topic:
    """Получить существующую тему или создать новую"""
    topic = get_topic_by_name(db, name)
    if not topic:
        topic = create_topic(db, name)
    return topic


def create_problem(
        db: Session,
        contest_id: int,
        index: str,
        name: str,
        rating: Optional[int] = None,
        tags: Optional[List[str]] = None
) -> Problem:
    """Создать новую задачу"""
    problem = Problem(
        contest_id=contest_id,
        index=index,
        name=name,
        rating=rating
    )
    if tags:
        problem.topics = [get_or_create_topic(db, tag) for tag in tags]
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


def get_or_create_topics_batch(db: Session, topic_names: List[str]) -> Dict[str, Topic]:
    """Получить или создать несколько тем за один запрос"""
    # Получаем существующие темы
    existing_topics = db.query(Topic).filter(Topic.name.in_(topic_names)).all()
    existing_topic_names = {topic.name for topic in existing_topics}

    # Создаем новые темы одним запросом
    new_topic_names = set(topic_names) - existing_topic_names
    if new_topic_names:
        new_topics = [Topic(name=name) for name in new_topic_names]
        db.bulk_save_objects(new_topics)
        db.commit()

        # Получаем созданные темы
        new_topics = db.query(Topic).filter(Topic.name.in_(new_topic_names)).all()
        existing_topics.extend(new_topics)

    return {topic.name: topic for topic in existing_topics}


def create_problems_batch(db: Session, problems_data: List[Dict]) -> None:
    """Создать несколько задач за один запрос"""
    try:
        # Собираем все уникальные теги
        all_tags = {tag for problem in problems_data for tag in problem.get('tags', [])}
        topics_map = get_or_create_topics_batch(db, list(all_tags))

        # Получаем существующие задачи
        contest_ids = [p['contest_id'] for p in problems_data]
        indices = [p['index'] for p in problems_data]
        existing_problems = db.query(Problem).filter(
            and_(
                Problem.contest_id.in_(contest_ids),
                Problem.index.in_(indices)
            )
        ).all()
        existing_problems_map = {
            (p.contest_id, p.index): p for p in existing_problems
        }

        # Подготавливаем новые задачи
        new_problems = []
        for problem_data in problems_data:
            key = (problem_data['contest_id'], problem_data['index'])
            if key not in existing_problems_map:
                problem = Problem(
                    contest_id=problem_data['contest_id'],
                    index=problem_data['index'],
                    name=problem_data['name'],
                    rating=problem_data.get('rating'),
                    solved_count=problem_data.get('solved_count', 0)
                )
                # Связываем с темами
                problem.topics = [topics_map[tag] for tag in problem_data.get('tags', [])]
                new_problems.append(problem)
            else:
                # Обновляем существующую задачу
                existing_problem = existing_problems_map[key]
                existing_problem.name = problem_data['name']
                existing_problem.rating = problem_data.get('rating')
                existing_problem.solved_count = problem_data.get('solved_count', 0)
                existing_problem.topics = [topics_map[tag] for tag in problem_data.get('tags', [])]

        # Сохраняем новые задачи
        if new_problems:
            db.bulk_save_objects(new_problems)

        # Фиксируем все изменения
        db.commit()

    except Exception as e:
        logger.error(f"Error in create_problems_batch: {str(e)}")
        db.rollback()
        raise


def get_problem(db: Session, contest_id: int, index: str) -> Optional[Problem]:
    """Получить задачу по contest_id и индексу"""
    return db.query(Problem).filter(
        and_(
            Problem.contest_id == contest_id,
            Problem.index == index
        )
    ).first()


def get_problems_by_filter(
        db: Session,
        rating: Optional[int] = None,
        topic: Optional[str] = None,
        limit: int = 10
) -> List[Problem]:
    """Получить задачи по фильтрам (сложность и/или тема)"""
    logger.debug(f"Searching for rating={rating}, topic={topic}")
    query = db.query(Problem)

    if rating:
        logger.debug("Applying rating filter")
        query = query.filter(Problem.rating == rating)

    if topic:
        logger.debug(f"Applying topic filter: {topic}")
        query = query.join(Problem.topics).filter(Topic.name == topic)

    result = query.order_by(Problem.solved_count.desc()).limit(limit).all()
    logger.debug(f"Found {len(result)} results")
    return result


def search_problems(db: Session, search_term: str) -> List[Problem]:
    """Поиск задач по названию"""
    return db.query(Problem).filter(
        or_(
            Problem.name.ilike(f"%{search_term}%"),
            Problem.index.ilike(f"%{search_term}%")
        )
    ).limit(10).all()


def get_problems_by_difficulty(db: Session, rating: int) -> List[Problem]:
    """Получить задачи по сложности"""
    return db.query(Problem).filter(Problem.rating == rating).all()


def get_problems_by_topic(db: Session, topic: str) -> List[Problem]:
    """Получить задачи по теме"""
    return db.query(Problem).join(Problem.topics).filter(Topic.name == topic).all()


def get_topics(db: Session) -> List[Topic]:
    """Получить список всех тем"""
    return db.query(Topic).all()


def get_problem_by_id(db: Session, problem_id: int) -> Optional[Problem]:
    """Получить задачу по ID"""
    return db.query(Problem).filter(Problem.id == problem_id).first()


def get_problems_count(db: Session) -> int:
    """Получить общее количество задач"""
    return db.query(Problem).count()


def get_problems_with_topics(db: Session) -> List[Problem]:
    """Получить все задачи с их темами"""
    return db.query(Problem).all()

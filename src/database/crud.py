from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from src.database.models import Problem, Topic


def get_problem(db: Session, contest_id: int, index: str) -> Optional[Problem]:
    """Получить задачу по contest_id и индексу"""
    return db.query(Problem).filter(
        and_(
            Problem.contest_id == contest_id,
            Problem.index == index
        )
    ).first()


def get_topic_by_name(db: Session, name: str) -> Optional[Topic]:
    """Получить тему по названию"""
    return db.query(Topic).filter(Topic.name == name).first()


def create_topic(db: Session, name: str) -> Topic:
    """Создать новую тему"""
    db_topic = Topic(name=name)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def get_or_create_topic(db: Session, name: str) -> Topic:
    """Получить или создать тему"""
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
        solved_count: int = 0,
        tags: List[str] = None
) -> Problem:
    """Создать новую задачу с привязкой тем"""
    if tags is None:
        tags = []

    db_problem = Problem(
        contest_id=contest_id,
        index=index,
        name=name,
        rating=rating,
        solved_count=solved_count
    )

    if tags:
        for tag in tags:
            topic = get_or_create_topic(db, tag)
            db_problem.topics.append(topic)

    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem


def get_problems_by_filter(
        db: Session,
        rating: Optional[int] = None,
        topic: Optional[str] = None,
        limit: int = 10
) -> List[Problem]:
    """Получить задачи по фильтрам (сложность и/или тема)"""
    query = db.query(Problem)

    if rating:
        query = query.filter(Problem.rating == rating)

    if topic:
        query = query.join(Problem.topics).filter(Topic.name == topic)

    return query.order_by(Problem.solved_count.desc()).limit(limit).all()


def search_problems(db: Session, search_term: str) -> List[Problem]:
    """Поиск задач по названию"""
    return db.query(Problem).filter(
        or_(
            Problem.name.ilike(f"%{search_term}%"),
            Problem.index.ilike(f"%{search_term}%")
        )
    ).limit(10).all()

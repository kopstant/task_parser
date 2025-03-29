import pytest
from sqlalchemy.orm import Session
from src.database.models import Problem, Topic
from src.database.crud import (
    get_problem,
    get_topic_by_name,
    create_topic,
    get_or_create_topic,
    create_problem,
    get_problems_by_filter,
    search_problems
)


def test_get_problem(db_session: Session):
    problem = Problem(contest_id=1, index='A', name='Test Problem')
    db_session.add(problem)
    db_session.commit()

    result = get_problem(db_session, 1, 'A')
    assert result is not None
    assert result.name == 'Test Problem'
    assert get_problem(db_session, 999, 'Z') is None


def test_get_topic_by_name(db_session: Session):
    topic = Topic(name='math')
    db_session.add(topic)
    db_session.commit()

    result = get_topic_by_name(db_session, 'math')
    assert result.name == 'math'
    assert get_topic_by_name(db_session, 'nonexistent') is None


def test_create_topic(db_session: Session):
    topic = create_topic(db_session, 'geometry')
    assert topic.id is not None
    assert topic.name == 'geometry'
    assert db_session.query(Topic).count() == 1


def test_get_or_create_topic(db_session: Session):
    topic1 = get_or_create_topic(db_session, 'math')
    assert topic1.id is not None

    topic2 = get_or_create_topic(db_session, 'math')
    assert topic1.id == topic2.id
    assert db_session.query(Topic).count() == 1


def test_create_problem(db_session: Session):
    problem1 = create_problem(
        db_session,
        contest_id=1,
        index='A',
        name='Problem A',
        rating=800
    )
    assert problem1.id is not None
    assert len(problem1.topics) == 0

    problem2 = create_problem(
        db_session,
        contest_id=2,
        index='B',
        name='Problem B',
        tags=['math', 'geometry']
    )
    assert len(problem2.topics) == 2
    assert {t.name for t in problem2.topics} == {'math', 'geometry'}


def test_get_problems_by_filter(db_session: Session):
    math = Topic(name='math')
    geometry = Topic(name='geometry')
    problem1 = Problem(contest_id=1, index='A', name='Easy', rating=800, solved_count=100)
    problem2 = Problem(contest_id=2, index='B', name='Hard', rating=1500, solved_count=50)
    problem1.topics.extend([math, geometry])
    problem2.topics.append(math)
    db_session.add_all([problem1, problem2, math, geometry])
    db_session.commit()

    assert len(get_problems_by_filter(db_session)) == 2
    assert len(get_problems_by_filter(db_session, rating=800)) == 1
    assert len(get_problems_by_filter(db_session, topic='math')) == 2
    assert len(get_problems_by_filter(db_session, topic='geometry')) == 1
    assert len(get_problems_by_filter(db_session, rating=1500, topic='math')) == 1
    assert len(get_problems_by_filter(db_session, limit=1)) == 1


def test_search_problems(db_session: Session):
    problems = [
        Problem(contest_id=1, index='A', name='Two Sum'),
        Problem(contest_id=2, index='B', name='Add Two Numbers'),
        Problem(contest_id=3, index='C1', name='Longest Substring')
    ]
    db_session.add_all(problems)
    db_session.commit()

    assert len(search_problems(db_session, 'Two')) == 2
    assert len(search_problems(db_session, 'sum')) == 1
    assert len(search_problems(db_session, 'C1')) == 1
    assert len(search_problems(db_session, 'nonexistent')) == 0

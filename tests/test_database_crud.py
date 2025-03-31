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
    search_problems,
    get_problems_by_difficulty,
    get_problems_by_topic,
    create_problems_batch,
    get_topics,
    get_problem_by_id,
    get_problems_count,
    get_problems_with_topics
)
from unittest.mock import MagicMock, create_autospec

# Тестовые данные
SAMPLE_TOPIC = Topic(name='math')
SAMPLE_PROBLEM = Problem(
    contest_id=1,
    index='A',
    name='Test Problem',
    rating=800,
    solved_count=100,
    topics=[SAMPLE_TOPIC]
)

SAMPLE_PROBLEMS_DATA = [
    {
        'contest_id': 1,
        'index': 'A',
        'name': 'Test Problem 1',
        'rating': 800,
        'solved_count': 100,
        'tags': ['math']
    },
    {
        'contest_id': 1,
        'index': 'B',
        'name': 'Test Problem 2',
        'rating': 1000,
        'solved_count': 50,
        'tags': ['math', 'dp']
    }
]


@pytest.fixture
def mock_session():
    session = create_autospec(Session, instance=True)
    query_mock = MagicMock()
    filter_mock = MagicMock()

    # Настраиваем возвращаемое значение для get_topic_by_name
    topic = Topic(id=1, name='math')
    filter_mock.first.return_value = topic

    query_mock.filter.return_value = filter_mock
    session.query.return_value = query_mock
    return session


def test_get_problem(mock_session):
    """Тест получения задачи по ID"""
    # Создаем мок для задачи
    problem = Problem(
        contest_id=1,
        index='A',
        name='Test Problem',
        rating=800
    )
    mock_session.query.return_value.filter.return_value.first.return_value = problem

    # Вызываем функцию
    result = get_problem(mock_session, 1, 'A')

    # Проверяем результат
    assert result.name == 'Test Problem'
    assert mock_session.query.call_count == 1


def test_get_topic_by_name(mock_session):
    """Тест получения темы по имени"""
    # Создаем мок для темы
    topic = Topic(name='math')
    mock_session.query.return_value.filter.return_value.first.return_value = topic

    # Вызываем функцию
    result = get_topic_by_name(mock_session, 'math')

    # Проверяем результат
    assert result.name == 'math'
    assert mock_session.query.call_count == 1


def test_create_topic(mock_session):
    """Тест создания темы"""
    # Вызываем функцию
    result = create_topic(mock_session, 'math')

    # Проверяем результат
    assert isinstance(result, Topic)
    assert result.name == 'math'
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_or_create_topic(mock_session):
    """Тест получения или создания темы"""
    # Настраиваем мок для проверки существования темы
    topic = Topic(name='math')
    mock_session.query.return_value.filter.return_value.first.return_value = topic

    # Вызываем функцию
    result = get_or_create_topic(mock_session, 'math')

    # Проверяем результат
    assert result.name == 'math'
    assert mock_session.query.call_count == 1


def test_create_problem(mock_session):
    """Тест создания задачи"""
    # Создаем мок для темы
    topic = Topic(name='math')
    mock_session.query.return_value.filter.return_value.first.return_value = topic

    # Вызываем функцию
    result = create_problem(
        mock_session,
        contest_id=1,
        index='A',
        name='Test Problem',
        rating=800,
        tags=['math']
    )

    # Проверяем результат
    assert isinstance(result, Problem)
    assert result.name == 'Test Problem'
    assert len(result.topics) == 1
    assert result.topics[0].name == 'math'
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_problems_by_filter(mock_session):
    """Тест получения задач по фильтрам"""
    # Создаем мок для задачи
    problem = Problem(
        contest_id=1,
        index='A',
        name='Test Problem',
        rating=800,
        solved_count=100
    )
    problem.topics = [Topic(name='math')]

    # Настраиваем мок для фильтра по сложности
    mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        problem]

    # Тест фильтра по сложности
    problems = get_problems_by_filter(mock_session, rating=800)
    assert len(problems) == 1
    assert problems[0].name == 'Test Problem'

    # Настраиваем мок для фильтра по теме
    mock_session.query.return_value \
        .join.return_value \
        .filter.return_value \
        .order_by.return_value \
        .limit.return_value \
        .all.return_value = [problem]

    # Тест фильтра по теме
    problems = get_problems_by_filter(mock_session, topic='math')
    assert len(problems) == 1
    assert problems[0].name == 'Test Problem'


def test_search_problems(mock_session):
    """Тест поиска задач"""
    # Создаем мок для задачи
    problem = Problem(
        contest_id=1,
        index='A',
        name='Test Problem',
        rating=800
    )
    mock_session.query.return_value.filter.return_value.limit.return_value.all.return_value = [problem]

    # Тест поиска по названию
    problems = search_problems(mock_session, 'Test')
    assert len(problems) == 1
    assert problems[0].name == 'Test Problem'


@pytest.fixture
def db_session():
    return MagicMock(spec=Session)


def test_get_problems_by_difficulty(db_session):
    """Тест получения задач по сложности"""
    # Подготавливаем тестовые данные
    db_session.query().filter().all.return_value = [SAMPLE_PROBLEM]

    # Вызываем функцию
    problems = get_problems_by_difficulty(db_session, 800)

    # Проверяем результат
    assert len(problems) == 1
    assert problems[0] == SAMPLE_PROBLEM


def test_get_problems_by_topic(db_session):
    """Тест получения задач по теме"""
    # Подготавливаем тестовые данные
    db_session.query().join().filter().all.return_value = [SAMPLE_PROBLEM]

    # Вызываем функцию
    problems = get_problems_by_topic(db_session, "math")

    # Проверяем результат
    assert len(problems) == 1
    assert problems[0] == SAMPLE_PROBLEM


def test_get_topics(db_session):
    """Тест получения списка тем"""
    # Подготавливаем тестовые данные
    db_session.query().all.return_value = [SAMPLE_TOPIC]

    # Вызываем функцию
    topics = get_topics(db_session)

    # Проверяем результат
    assert len(topics) == 1
    assert topics[0] == SAMPLE_TOPIC


def test_get_problem_by_id(db_session):
    """Тест получения задачи по ID"""
    # Подготавливаем тестовые данные
    db_session.query().filter().first.return_value = SAMPLE_PROBLEM

    # Вызываем функцию
    problem = get_problem_by_id(db_session, 1)

    # Проверяем результат
    assert problem == SAMPLE_PROBLEM


def test_get_problems_count(db_session):
    """Тест получения количества задач"""
    # Подготавливаем тестовые данные
    db_session.query().count.return_value = 10

    # Вызываем функцию
    count = get_problems_count(db_session)

    # Проверяем результат
    assert count == 10


def test_get_problems_with_topics(db_session):
    """Тест получения задач с темами"""
    # Подготавливаем тестовые данные
    db_session.query().all.return_value = [SAMPLE_PROBLEM]

    # Вызываем функцию
    problems = get_problems_with_topics(db_session)

    # Проверяем результат
    assert len(problems) == 1
    assert problems[0] == SAMPLE_PROBLEM


def test_create_problems_batch_error(db_session):
    """Тест обработки ошибок при создании пакета задач"""
    # Подготавливаем тестовые данные с некорректными данными
    invalid_data = [
        {
            'contest_id': None,  # Некорректные данные
            'index': None,
            'name': None,
            'rating': None,
            'solved_count': None,
            'tags': None
        }
    ]

    # Мокаем ошибку при сохранении
    db_session.commit.side_effect = Exception("Database error")

    # Вызываем функцию и проверяем, что она обрабатывает ошибку
    with pytest.raises(Exception):
        create_problems_batch(db_session, invalid_data)

    # Проверяем, что был сделан rollback
    db_session.rollback.assert_called_once()

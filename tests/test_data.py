from src.database.models import Problem, Topic

# Создаем тестовые объекты
test_topic = Topic(name='math')
test_problem = Problem(
    contest_id=1,
    index='A',
    name='Test Problem',
    rating=800,
    solved_count=100
)
test_problem.topics.append(test_topic)

SAMPLE_PROBLEMS = [
    {
        'contestId': 1,
        'index': 'A',
        'name': 'Test Problem',
        'rating': 800,
        'tags': ['math']
    },
    {
        'contestId': 1,
        'index': 'B',
        'name': 'Problem B',
        'rating': 1000,
        'tags': ['dp']
    }
]

SAMPLE_STATISTICS = [
    {
        'contestId': 1,
        'index': 'A',
        'solvedCount': 100
    },
    {
        'contestId': 1,
        'index': 'B',
        'solvedCount': 200
    }
]

SAMPLE_DB_PROBLEMS = [test_problem]
SAMPLE_DB_PROBLEM = test_problem

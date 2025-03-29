import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.database.models import Problem, Topic
from src.config import config


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(config.TEST_DATABASE_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        for table in reversed(Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()
        self.session.close()

    def test_problem_creation(self):
        problem = Problem(
            contest_id=1,
            index='A',
            name='Test Problem',
            rating=800,
            solved_count=100
        )
        self.session.add(problem)
        self.session.commit()

        db_problem = self.session.query(Problem).first()
        self.assertEqual(db_problem.name, 'Test Problem')
        self.assertEqual(db_problem.rating, 800)

    def test_topic_creation(self):
        topic_name = 'math'
        # Проверяем, есть ли уже такая тема
        existing_topic = self.session.query(Topic).filter_by(name=topic_name).first()
        if not existing_topic:
            topic = Topic(name=topic_name)
            self.session.add(topic)
            self.session.commit()

        db_topic = self.session.query(Topic).first()
        self.assertEqual(db_topic.name, 'math')

    def test_problem_topic_relationship(self):
        # Создаем и сохраняем тему
        topic = Topic(name='math')
        self.session.add(topic)
        self.session.commit()

        # Проверяем, что тема сохранена
        db_topic = self.session.query(Topic).first()
        self.assertEqual(db_topic.name, 'math')

        # Создаем задачу
        problem = Problem(
            contest_id=1,
            index='A',
            name='Test Problem'
        )

        # Добавляем тему к задаче
        problem.topics.append(db_topic)  # Используем тему из базы
        self.session.add(problem)
        self.session.commit()

        # Обновляем объекты из базы
        self.session.refresh(problem)
        db_problem = self.session.query(Problem).first()

        # Отладочный вывод
        print(f"Problem topics: {db_problem.topics}")
        print(f"Topic problems: {db_topic.problems}")

        # Проверяем связь с обеих сторон
        self.assertEqual(len(db_problem.topics), 1)
        self.assertEqual(len(db_topic.problems), 1)
        self.assertEqual(db_problem.topics[0].name, 'math')
        self.assertEqual(db_topic.problems[0].name, 'Test Problem')

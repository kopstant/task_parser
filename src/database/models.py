from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Table
from src.database.base import Base

# Ассоциативная таблица для связи многие-ко-многим между задачами и темами
problem_topic_association = Table(
    'problem_topic_association',
    Base.metadata,
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True)
)


class Problem(Base):
    """Модель задачи с Codeforces"""
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, nullable=False)
    index = Column(String(5), nullable=False)  # Например, 'A', 'B1', 'C2'
    name = Column(String(255), nullable=False)
    rating = Column(Integer)  # Сложность задачи (800, 1000 и т.д.)
    solved_count = Column(Integer, default=0)  # Количество решений

    # Связь многие-ко-многим с темами
    topics = relationship(
        "Topic",
        secondary=problem_topic_association,
        back_populates="problems",
        cascade="all, delete"  # Добавлено каскадирование
    )

    def __repr__(self):
        return f"<Problem {self.contest_id}{self.index}: {self.name}>"


class Topic(Base):
    """Модель темы задачи (теги Codeforces)"""
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # Связь многие-ко-многим с задачами
    problems = relationship(
        "Problem",
        secondary=problem_topic_association,
        back_populates="topics"
    )

    def __repr__(self):
        return f"<Topic {self.name}>"

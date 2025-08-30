# models/kpi.py

import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Mövcud User modelini import etmək üçün User sinifini tapmalısınız
# Əgər Base obyekti mərkəzi bir yerdədirsə, onu import edin.
# Deyilsə, burada yeni bir Base yaradın.
try:
    from models.user import Base # Proyektin strukturuna görə bu dəyişə bilər
except ImportError:
    Base = declarative_base()


class EvaluationPeriod(Base):
    __tablename__ = 'evaluation_periods'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    evaluations = relationship("Evaluation", back_populates="period")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(String(100))

class EvaluationStatus(enum.Enum):
    PENDING = "GÖZLƏMƏDƏ"
    COMPLETED = "TAMAMLANMIŞ"

class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('evaluation_periods.id'))
    evaluated_user_id = Column(Integer, ForeignKey('users.id'))
    evaluator_user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING)
    period = relationship("EvaluationPeriod", back_populates="evaluations")
    answers = relationship("Answer", back_populates="evaluation")

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey('evaluations.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    score = Column(Integer)
    comment = Column(Text)
    evaluation = relationship("Evaluation", back_populates="answers")
    question = relationship("Question")
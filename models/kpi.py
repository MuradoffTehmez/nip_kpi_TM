# models/kpi.py

import enum
import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Enum, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Layihənizdəki user.py faylından Base obyektini import etməyə çalışırıq.
# Bu, bütün modellərin eyni metadata-nı paylaşmasını təmin edir.
try:
    from models.user import Base
except ImportError:
    # Əgər mərkəzi Base yoxdursa, yeni birini yaradırıq.
    Base = declarative_base()

class EvaluationPeriod(Base):
    """ Qiymətləndirmə dövrü (məsələn, "2025 - I Rüblük") """
    __tablename__ = 'evaluation_periods'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    
    evaluations = relationship("Evaluation", back_populates="period", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EvaluationPeriod(name='{self.name}')>"

class Question(Base):
    """ Qiymətləndirmə üçün suallar """
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(String(100), default="Ümumi")
    weight = Column(Float, default=1.0)  # Sualın çəkisi
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Question(text='{self.text[:30]}...')>"

class EvaluationStatus(enum.Enum):
    PENDING = "GÖZLƏMƏDƏ"
    SELF_EVAL_COMPLETED = "İŞÇİ DƏYƏRLƏNDİRDİ"
    MANAGER_REVIEW_COMPLETED = "RƏHBƏR DƏYƏRLƏNDİRDİ"
    FINALIZED = "YEKUNLAŞDIRILDI"

class Evaluation(Base):
    """ Konkret qiymətləndirmə tapşırığı (kim kimi qiymətləndirəcək) """
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True)
    
    period_id = Column(Integer, ForeignKey('evaluation_periods.id'), nullable=False)
    evaluated_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    evaluator_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING, nullable=False)
    
    period = relationship("EvaluationPeriod", back_populates="evaluations")
    evaluated_user = relationship("User", foreign_keys=[evaluated_user_id])
    evaluator_user = relationship("User", foreign_keys=[evaluator_user_id])
    
    answers = relationship("Answer", back_populates="evaluation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Evaluation(id={self.id}, status='{self.status.value}')>"

class Answer(Base):
    """ Verilmiş cavablar """
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True)
    
    evaluation_id = Column(Integer, ForeignKey('evaluations.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    
    score = Column(Integer, nullable=False)
    comment = Column(Text)
    author_role = Column(String(20), nullable=False, default='employee')  # 'employee' or 'manager'
    
    evaluation = relationship("Evaluation", back_populates="answers")
    question = relationship("Question")

    def __repr__(self):
        return f"<Answer(score={self.score}, author_role='{self.author_role}')>"
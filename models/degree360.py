# models/degree360.py

import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

try:
    from models.user import Base
except ImportError:
    from database import Base

# Association table for 360-degree questions and competencies
from sqlalchemy import Table
degree360_question_competency_association = Table(
    'degree360_question_competency',
    Base.metadata,
    Column('question_id', Integer, ForeignKey('degree360_questions.id'), primary_key=True),
    Column('competency_id', Integer, ForeignKey('competencies.id'), primary_key=True),
    extend_existing=True
)

class Degree360Session(Base):
    """
    360 dərəcə qiymətləndirmə sessiyası.
    Hər bir sessiya müəyyən bir dövrə və qiymətləndiriləcək şəxs üzrə olur.
    """
    __tablename__ = 'degree360_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Sessiyanın adı (məsələn, "2025-ci il 360° Qiymətləndirməsi")
    evaluated_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Qiymətləndiriləcək şəxs
    evaluator_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Sessiyanı yaradan rəhbər
    start_date = Column(Date, nullable=False)  # Başlama tarixi
    end_date = Column(Date, nullable=False)  # Bitmə tarixi
    is_anonymous = Column(Boolean, default=True)  # Anonimlik parametri
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    evaluated_user = relationship("User", foreign_keys=[evaluated_user_id], backref="evaluated_360_sessions")
    evaluator_user = relationship("User", foreign_keys=[evaluator_user_id], backref="evaluator_360_sessions")
    participants = relationship("Degree360Participant", back_populates="session", cascade="all, delete-orphan")
    questions = relationship("Degree360Question", back_populates="session", cascade="all, delete-orphan")

class Degree360ParticipantRole(enum.Enum):
    """
    360 dərəcə qiymətləndirmədə iştirakçıların rolu.
    """
    SELF = "Özünü qiymətləndirən"
    MANAGER = "Rəhbər"
    PEER = "Həmkar"
    SUBORDINATE = "Tabeçil"
    CUSTOMER = "Müştəri"

class Degree360Participant(Base):
    """
    360 dərəcə qiymətləndirmədə iştirakçılar.
    Hər bir qiymətləndiriləcək şəxs üçün müxtəlif roldakı qiymətləndiricilər olur.
    """
    __tablename__ = 'degree360_participants'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('degree360_sessions.id'), nullable=False)
    evaluator_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Qiymətləndirən şəxs
    role = Column(Enum(Degree360ParticipantRole), nullable=False)  # Qiymətləndiricinin rolu
    status = Column(String, default="PENDING")  # PENDING, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    session = relationship("Degree360Session", back_populates="participants")
    evaluator_user = relationship("User", foreign_keys=[evaluator_user_id], backref="evaluator_360_participations")
    answers = relationship("Degree360Answer", back_populates="participant", cascade="all, delete-orphan")

class Degree360Question(Base):
    """
    360 dərəcə qiymətləndirmə üçün suallar.
    Hər bir sessiya öz suallarına malikdir.
    """
    __tablename__ = 'degree360_questions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('degree360_sessions.id'), nullable=False)
    text = Column(Text, nullable=False)  # Sualın mətni
    category = Column(String(100), default="Ümumi")  # Kateqoriya
    weight = Column(Integer, default=1)  # Sualın çəkisi (1-5 arası)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Competency relationship
    competencies = relationship(
        "Competency",
        secondary=degree360_question_competency_association
    )
    
    # Relationship
    session = relationship("Degree360Session", back_populates="questions")
    answers = relationship("Degree360Answer", back_populates="question", cascade="all, delete-orphan")

class Degree360Answer(Base):
    """
    360 dərəcə qiymətləndirmədə verilmiş cavablar.
    Hər bir iştirakçı hər bir suala cavab verir.
    """
    __tablename__ = 'degree360_answers'
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey('degree360_participants.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('degree360_questions.id'), nullable=False)
    score = Column(Integer, nullable=False)  # Cavab balları (1-5 arası)
    comment = Column(Text)  # Şərh (vacib deyil)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    participant = relationship("Degree360Participant", back_populates="answers")
    question = relationship("Degree360Question", back_populates="answers")
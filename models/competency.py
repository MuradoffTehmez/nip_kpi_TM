"""Competency models for the HR management system."""

from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# Import models to avoid circular imports
from models.kpi import Question as KPIQuestion, kpi_question_competency_association
from models.degree360 import Degree360Question, degree360_question_competency_association


class Competency(Base):
    """Model representing a competency in the organization."""
    
    __tablename__ = 'competencies'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # e.g., "Leadership", "Technical", "Communication"
    
    # Relationships
    kpi_questions = relationship(
        "KPIQuestion",
        secondary=kpi_question_competency_association
    )
    
    degree360_questions = relationship(
        "Degree360Question",
        secondary=degree360_question_competency_association
    )
    
    def __repr__(self):
        return f"<Competency(id={self.id}, name='{self.name}', category='{self.category}')>"
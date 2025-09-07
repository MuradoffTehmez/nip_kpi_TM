# models/pdp.py

from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

try:
    from models.user import Base
except ImportError:
    from database import Base

class DevelopmentPlan(Base):
    __tablename__ = "development_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED, CANCELLED
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id], backref="development_plans")
    manager = relationship("User", foreign_keys=[manager_id])
    evaluation = relationship("Evaluation", backref="development_plan")
    plan_items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")

class PlanItem(Base):
    __tablename__ = "plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("development_plans.id"), nullable=False)
    goal = Column(String, nullable=False)  # Hədəf
    actions_to_take = Column(String, nullable=False)  # Atılacaq addımlar
    deadline = Column(Date, nullable=False)  # Son tarix
    is_completed = Column(Boolean, default=False, server_default=text("false"))
    progress = Column(Integer, default=0)  # 0-100 arası dəyər
    status = Column(String, default="Başlanmayıb")  # "Başlanmayıb", "Davam edir", "Tamamlanıb"
    
    # Relationship
    plan = relationship("DevelopmentPlan", back_populates="plan_items")
    comments = relationship("PlanItemComment", back_populates="plan_item", cascade="all, delete-orphan")

class PlanItemComment(Base):
    __tablename__ = "plan_item_comments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("plan_items.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    comment_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    plan_item = relationship("PlanItem", back_populates="comments")
    author = relationship("User", backref="plan_item_comments")
from sqlalchemy import Integer, Float, Date, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

from models.user import User
from models.indicator import Indicator


class Performance(Base):
    __tablename__ = "performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(column=User.id, name="fk_performance_user_id", ondelete="CASCADE"), nullable=False)
    indicator_id: Mapped[int] = mapped_column(Integer, ForeignKey(column=Indicator.id, name="fk_performance_indicator_id", ondelete="CASCADE"), nullable=False)
    evaluation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluation_month: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    weighted_points: Mapped[float] = mapped_column(Float, nullable=False)
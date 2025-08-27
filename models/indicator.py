from sqlalchemy import Integer, String, Float, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Indicator(Base):
    __tablename__ = "indicator"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
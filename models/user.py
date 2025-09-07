from sqlalchemy import Integer, String, Boolean, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from passlib.context import CryptContext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user_profile import UserProfile

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)

    # Relationship to UserProfile
    profile = relationship("UserProfile", back_populates="user", uselist=False, lazy="select")
    
    # Self-referential relationship for manager/subordinates
    manager = relationship("User", remote_side=[id], back_populates="subordinates")
    subordinates = relationship("User", back_populates="manager")

    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password"""
        return pwd_context.verify(password, self.password)

    def get_full_name(self) -> str:
        """Get the full name from the associated profile"""
        if self.profile:
            return self.profile.full_name
        return "Naməlum"

from sqlalchemy import Integer, String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password"""
        return pwd_context.verify(password, self.password)

# services/user_service.py

from database import get_db
from models.user import User
from models.user_profile import UserProfile

class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        """İstifadəçini ID-sinə görə əldə edir."""
        with get_db() as session:
            return session.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_profile_by_user_id(user_id):
        """İstifadəçinin profilini istifadəçi ID-sinə görə əldə edir."""
        with get_db() as session:
            return session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    @staticmethod
    def get_all_active_users():
        """Bütün aktiv istifadəçiləri əldə edir."""
        with get_db() as session:
            return session.query(User).filter(User.is_active == True).all()

    @staticmethod
    def get_subordinates(manager_id):
        """Menecerə tabe olan istifadəçiləri əldə edir."""
        with get_db() as session:
            return session.query(User).filter(User.manager_id == manager_id, User.is_active == True).all()
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
            
    @staticmethod
    def get_all_users_with_profiles():
        """Bütün istifadəçiləri və onların profillərini əldə edir."""
        with get_db() as session:
            users = session.query(User).all()
            user_data = []
            for user in users:
                profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
                user_data.append({
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "is_active": user.is_active,
                    "manager_id": user.manager_id,
                    "full_name": profile.full_name if profile else "",
                    "position": profile.position if profile else "",
                    "department": profile.department if profile else ""
                })
            return user_data
            
    @staticmethod
    def update_user_profile(user_id, data):
        """İstifadəçinin profilini yeniləyir."""
        with get_db() as session:
            # İstifadəçini yenilə
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                if "username" in data:
                    user.username = data["username"]
                if "role" in data:
                    user.role = data["role"]
                if "is_active" in data:
                    user.is_active = data["is_active"]
                if "manager_id" in data:
                    user.manager_id = data["manager_id"] if data["manager_id"] else None
            
            # Profili yenilə
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                if "full_name" in data:
                    profile.full_name = data["full_name"]
                if "position" in data:
                    profile.position = data["position"]
                if "department" in data:
                    profile.department = data["department"] if data["department"] else None
            else:
                # Əgər profil yoxdursa, yenisini yarat
                profile = UserProfile(
                    user_id=user_id,
                    full_name=data.get("full_name", ""),
                    position=data.get("position", ""),
                    department=data.get("department", "")
                )
                session.add(profile)
            
            session.commit()
            return user, profile
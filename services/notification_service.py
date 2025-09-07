# services/notification_service.py

from database import get_db
from models.notification import Notification
from models.user import User

class NotificationService:
    @staticmethod
    def create_notification(user_id: int, message: str) -> Notification:
        """Yeni bildiriş yaradır."""
        with get_db() as session:
            notification = Notification(
                user_id=user_id,
                message=message
            )
            session.add(notification)
            session.commit()
            session.refresh(notification)
            return notification

    @staticmethod
    def get_unread_notifications(user_id: int):
        """İstifadəçinin oxunmamış bildirişlərini qaytarır."""
        with get_db() as session:
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).all()

    @staticmethod
    def mark_as_read(notification_id: int):
        """Bildirişi oxunmuş kimi qeyd edir."""
        with get_db() as session:
            notification = session.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.is_read = True
                session.commit()
                
    @staticmethod
    def mark_all_as_read(user_id: int):
        """İstifadəçinin bütün bildirişlərini oxunmuş kimi qeyd edir."""
        with get_db() as session:
            notifications = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).all()
            for notification in notifications:
                notification.is_read = True
            session.commit()
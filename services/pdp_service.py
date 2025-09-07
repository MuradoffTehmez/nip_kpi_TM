# services/pdp_service.py

from database import get_db
from models.pdp import DevelopmentPlan, PlanItem
from datetime import date

class PDPService:
    @staticmethod
    def create_development_plan(user_id: int, evaluation_id: int, manager_id: int = None) -> DevelopmentPlan:
        """Yeni inkişaf planı yaradır."""
        with get_db() as session:
            plan = DevelopmentPlan(
                user_id=user_id,
                evaluation_id=evaluation_id,
                manager_id=manager_id
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            return plan

    @staticmethod
    def get_development_plan_by_id(plan_id: int) -> DevelopmentPlan:
        """Planı ID-sinə görə qaytarır."""
        with get_db() as session:
            return session.query(DevelopmentPlan).filter(DevelopmentPlan.id == plan_id).first()

    @staticmethod
    def get_development_plans_for_user(user_id: int):
        """İstifadəçinin bütün inkişaf planlarını qaytarır."""
        with get_db() as session:
            return session.query(DevelopmentPlan).filter(DevelopmentPlan.user_id == user_id).all()

    @staticmethod
    def get_active_development_plans_for_user(user_id: int):
        """İstifadəçinin aktiv inkişaf planlarını qaytarır."""
        with get_db() as session:
            return session.query(DevelopmentPlan).filter(
                DevelopmentPlan.user_id == user_id,
                DevelopmentPlan.status == "ACTIVE"
            ).all()

    @staticmethod
    def update_development_plan_status(plan_id: int, status: str):
        """Planın statusunu yeniləyir."""
        with get_db() as session:
            plan = session.query(DevelopmentPlan).filter(DevelopmentPlan.id == plan_id).first()
            if plan:
                plan.status = status
                session.commit()

    @staticmethod
    def create_plan_item(plan_id: int, goal: str, actions_to_take: str, deadline: date) -> PlanItem:
        """Plan üçün yeni hədəf yaradır."""
        with get_db() as session:
            item = PlanItem(
                plan_id=plan_id,
                goal=goal,
                actions_to_take=actions_to_take,
                deadline=deadline
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    @staticmethod
    def get_plan_items_for_plan(plan_id: int):
        """Plan üçün bütün hədəfləri qaytarır."""
        with get_db() as session:
            return session.query(PlanItem).filter(PlanItem.plan_id == plan_id).all()

    @staticmethod
    def mark_plan_item_as_completed(item_id: int):
        """Hədəfi tamamlanmış kimi qeyd edir."""
        with get_db() as session:
            item = session.query(PlanItem).filter(PlanItem.id == item_id).first()
            if item:
                item.is_completed = True
                session.commit()

    @staticmethod
    def delete_plan_item(item_id: int):
        """Hədəfi silir."""
        with get_db() as session:
            item = session.query(PlanItem).filter(PlanItem.id == item_id).first()
            if item:
                session.delete(item)
                session.commit()
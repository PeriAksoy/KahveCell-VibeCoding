import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Plan, Subscription
from app.models.enums import PlanType, SubscriptionStatus


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_plans(self) -> list[Plan]:
        return list(self.db.scalars(select(Plan).order_by(Plan.monthly_price)))

    def get_plan_by_code(self, code: PlanType) -> Plan | None:
        return self.db.scalar(select(Plan).where(Plan.code == code))

    def get_active_for_user(self, user_id: uuid.UUID) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE
            )
        )

    def add(self, subscription: Subscription) -> None:
        self.db.add(subscription)
        self.db.flush()

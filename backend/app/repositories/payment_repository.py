import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment
from app.models.enums import PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, payment: Payment) -> None:
        self.db.add(payment)
        self.db.flush()

    def list_for_user(self, user_id: uuid.UUID, limit: int, offset: int) -> list[Payment]:
        return list(
            self.db.scalars(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def last_successful(self, user_id: uuid.UUID) -> Payment | None:
        return self.db.scalar(
            select(Payment)
            .where(Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )

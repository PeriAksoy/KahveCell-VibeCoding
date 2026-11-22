import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models import Order, Plan, Shop, Subscription
from app.models.enums import ACTIVE_ORDER_STATUSES, OrderStatus

# Sipariş çıktısı için gereken ilişkileri baştan yükler (sipariş başına ekstra sorgu atılmasın).
_LOAD = (
    selectinload(Order.shop),
    selectinload(Order.product),
    selectinload(Order.user),
    selectinload(Order.subscription).selectinload(Subscription.plan),
)


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, order: Order) -> None:
        self.db.add(order)
        self.db.flush()

    def get(self, order_id: uuid.UUID) -> Order | None:
        return self.db.scalar(select(Order).where(Order.id == order_id).options(*_LOAD))

    def consume_credit(self, subscription_id: uuid.UUID) -> bool:
        """Hakkı TEK bir atomik sorguyla düşer. Hak kalmadıysa hiçbir satır güncellenmez ve False döner;
        böylece aynı anda gelen iki istek son hakkı iki kez harcayamaz."""
        result = self.db.execute(
            update(Subscription)
            .where(Subscription.id == subscription_id, Subscription.remaining_credits > 0)
            .values(remaining_credits=Subscription.remaining_credits - 1)
        )
        return result.rowcount == 1

    def list_for_customer(
        self, user_id: uuid.UUID, status: OrderStatus | None, limit: int, offset: int
    ) -> list[Order]:
        query = select(Order).where(Order.user_id == user_id)
        if status is not None:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).options(*_LOAD)
        return list(self.db.scalars(query))

    def list_for_owner(self, owner_id: uuid.UUID, status: OrderStatus | None, limit: int, offset: int) -> list[Order]:
        """Dükkân sahibinin siparişleri. Durum verilmezse yalnızca bitmemiş siparişler (kuyruk) gelir."""
        query = (
            select(Order)
            .join(Shop, Order.shop_id == Shop.id)
            .join(Subscription, Order.subscription_id == Subscription.id)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(Shop.owner_id == owner_id)
            .where(Order.status == status if status is not None else Order.status.in_(ACTIVE_ORDER_STATUSES))
        )
        if status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            query = query.order_by(Order.created_at.desc())  # biten işler: en yeni önce
        else:
            query = query.order_by(Plan.has_priority.desc(), Order.created_at.asc())  # kuyruk: öncelikli, sonra en eski
        return list(self.db.scalars(query.limit(limit).offset(offset).options(*_LOAD)))

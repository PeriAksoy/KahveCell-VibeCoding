import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CupSize, OrderStatus
from app.models.user import utcnow


class Order(Base):
    """Bir sipariş = bir kahve = 1 abonelik hakkı."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("sugar_level BETWEEN 0 AND 5", name="ck_order_sugar"),
        CheckConstraint("extra_shots BETWEEN 0 AND 4", name="ck_order_shots"),
        Index("ix_orders_user_created", "user_id", "created_at"),  # sipariş geçmişi
        Index("ix_orders_shop_status", "shop_id", "status"),  # dükkân paneli: bekleyenler
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    # Hangi abonelikten hak düşüldü (hesap verilebilirlik için)
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))

    # Özelleştirmeler
    size: Mapped[CupSize] = mapped_column(Enum(CupSize, native_enum=False, length=1), default=CupSize.M)
    sugar_level: Mapped[int] = mapped_column(Integer, default=0)
    milk_type: Mapped[str | None] = mapped_column(String(30))  # örn. "tam yağlı", "yulaf", "badem"
    extra_shots: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20), default=OrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="orders")
    shop = relationship("Shop", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    subscription = relationship("Subscription", back_populates="orders")

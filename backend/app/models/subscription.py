import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PlanType, SubscriptionStatus
from app.models.user import utcnow


class Plan(Base):
    """Satışa sunulan paketler (Starter / Premium / Unlimited). Fiyatlar kodda değil burada durur."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[PlanType] = mapped_column(
        Enum(PlanType, native_enum=False, length=20), unique=True
    )
    name: Mapped[str] = mapped_column(String(50))
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # NULL = sınırsız (Unlimited paketi)
    monthly_credits: Mapped[int | None] = mapped_column(Integer)
    guest_passes: Mapped[int] = mapped_column(Integer, default=0)
    has_priority: Mapped[bool] = mapped_column(Boolean, default=False)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        # Bir kullanıcının aynı anda en fazla BİR aktif aboneliği olabilir.
        Index(
            "uq_one_active_subscription_per_user",
            "user_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id"))
    # NULL = sınırsız paket; diğerlerinde kalan kahve hakkı
    remaining_credits: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, native_enum=False, length=20),
        default=SubscriptionStatus.ACTIVE,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    orders = relationship("Order", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")

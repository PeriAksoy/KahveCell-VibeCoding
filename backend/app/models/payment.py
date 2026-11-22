import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PaymentStatus
from app.models.user import utcnow


class Payment(Base):
    """Ödeme geçmişi (simülasyon). Başarısız denemeler de kaydedilir."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id"))
    # Ödeme başarısızsa abonelik oluşmaz, bu yüzden boş olabilir.
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subscriptions.id"))
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, native_enum=False, length=20))
    card_last4: Mapped[str] = mapped_column(String(4))  # kartın tamamı ASLA saklanmaz
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    subscription = relationship("Subscription", back_populates="payments")

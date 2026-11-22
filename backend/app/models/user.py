import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    # Ad ve e-posta ilk girişteki "profil tamamlama" adımında doldurulur, o yüzden boş olabilir.
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), default=UserRole.CUSTOMER
    )
    # Tercih edilen kahve türleri ve alerjenler: {"coffees": [...], "allergens": [...]}
    preferences: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    orders = relationship("Order", back_populates="user")
    shops = relationship("Shop", back_populates="owner")

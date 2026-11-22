from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.core.database import Base
from app.models.user import utcnow


class RefreshToken(Base):
    """Verilmiş yenileme biletlerinin kaydı. Çıkış yapılınca veya yenilenince 'revoked_at' dolar,
    böylece eski bilet bir daha kullanılamaz."""

    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

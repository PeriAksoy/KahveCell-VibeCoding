import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_shop_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_shop_longitude"),
        # Konum sorgusu önce bu "kutuyla" daraltılır, sonra Haversine ile kesin mesafe hesaplanır.
        Index("ix_shops_location", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    # Çalışma saatleri "HH:MM" metni. Açık/kapalı durumu bunlardan hesaplanır.
    opens_at: Mapped[str] = mapped_column(String(5), default="08:00")
    closes_at: Mapped[str] = mapped_column(String(5), default="22:00")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    owner = relationship("User", back_populates="shops")
    products = relationship("Product", back_populates="shop")
    orders = relationship("Order", back_populates="shop")


class Product(Base):
    """Bir dükkânın menüsündeki ürün (kahve türü)."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    # Abonelik hakkıyla alınan kahvenin liste değeri (raporlama ve ek shot/boy farkı için).
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    shop = relationship("Shop", back_populates="products")
    orders = relationship("Order", back_populates="product")

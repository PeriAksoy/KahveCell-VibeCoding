import uuid

from pydantic import BaseModel, ConfigDict, computed_field

from app.core.categories import category_for
from app.schemas.common import Money


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    base_price: Money
    image_url: str | None
    is_available: bool

    @computed_field
    @property
    def category(self) -> str:
        """espresso | filter | cold | other (ürün adından türetilir)"""
        return category_for(self.name)


class ShopOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    latitude: float
    longitude: float
    opens_at: str
    closes_at: str
    is_open: bool  # şu an (Türkiye saatiyle) açık mı
    rating: float
    image_url: str | None
    distance_km: float | None  # konum gönderildiyse kuş uçuşu mesafe, yoksa null


class ShopDetailOut(ShopOut):
    menu: list[ProductOut]


class ShopListResult(BaseModel):
    items: list[ShopOut]
    total: int  # limit/offset öncesi toplam sonuç sayısı

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CupSize, MilkType, OrderStatus


class QrPayload(BaseModel):
    """Case 13.2'deki QR içeriği. Bu alanlar QR koda JSON olarak yazılır; 'signature' sahteciliği önler."""

    order_id: uuid.UUID
    user_id: uuid.UUID
    shop_id: uuid.UUID
    created_at: str = Field(examples=["2026-11-22T14:30:00.000Z"])
    signature: str = Field(description="HMAC-SHA256 imzası (hex)")


class OrderCreate(BaseModel):
    shop_id: uuid.UUID
    product_id: uuid.UUID
    size: CupSize = CupSize.M
    sugar_level: int = Field(0, ge=0, le=5, description="0 = şekersiz")
    milk_type: MilkType | None = Field(None, description="Boş = sütsüz")
    extra_shots: int = Field(0, ge=0, le=4)


class ShopBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str


class ProductBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class OrderOut(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    status_label: str
    shop: ShopBrief
    product: ProductBrief
    size: CupSize
    sugar_level: int
    milk_type: MilkType | None
    extra_shots: int
    customer_name: str  # profil doldurulmamışsa "Müşteri"
    is_priority: bool = Field(description="Öncelikli paket (Unlimited) müşterisi mi; dükkân kuyruğunda öne alınır")
    created_at: datetime
    updated_at: datetime
    # QR yalnızca siparişin sahibi olan müşteriye gösterilir.
    qr_payload: QrPayload | None = None
    qr_image: str | None = Field(None, description="QR kodun PNG resmi (data URI, <img src=...> ile gösterilir)")


class OrderCreated(BaseModel):
    order: OrderOut
    remaining_credits: int | None = Field(description="Sipariş sonrası kalan hak; null = sınırsız paket")


class StatusUpdate(BaseModel):
    status: OrderStatus
    qr: QrPayload | None = Field(None, description="Yalnızca COMPLETED (teslim) için zorunlu: müşterinin QR içeriği")


class VerifyQrRequest(BaseModel):
    qr: QrPayload


class VerifyQrResult(BaseModel):
    authentic: bool
    can_deliver: bool
    message: str
    order: OrderOut

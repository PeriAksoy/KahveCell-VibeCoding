import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import PaymentStatus
from app.schemas.common import Money


class CardInput(BaseModel):
    """Kart formu. Kartın tamamı hiçbir yere kaydedilmez, yalnızca son 4 hane tutulur."""

    model_config = ConfigDict(str_strip_whitespace=True)

    card_holder: str = Field(min_length=2, max_length=100, examples=["Test Kullanıcı"])
    card_number: str = Field(examples=["4242 4242 4242 4242"])
    expiry_month: int = Field(ge=1, le=12, examples=[12])
    expiry_year: int = Field(ge=2000, le=2100, examples=[2030])
    cvc: str = Field(pattern=r"^\d{3,4}$", examples=["123"])

    @field_validator("card_number")
    @classmethod
    def _clean_number(cls, value: str) -> str:
        digits = re.sub(r"[\s-]", "", value)
        if not digits.isdigit() or len(digits) != 16:
            raise ValueError("Kart numarası 16 haneli olmalıdır.")
        return digits

    @model_validator(mode="after")
    def _not_expired(self):
        today = date.today()
        if (self.expiry_year, self.expiry_month) < (today.year, today.month):
            raise ValueError("Kartın son kullanma tarihi geçmiş.")
        return self


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: str
    amount: Money
    status: PaymentStatus
    card_last4: str
    subscription_id: uuid.UUID | None
    created_at: datetime

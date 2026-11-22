import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.models.enums import PlanType, SubscriptionStatus
from app.schemas.common import Money
from app.schemas.payment import CardInput, PaymentOut


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: PlanType
    name: str
    monthly_price: Money
    monthly_credits: int | None  # None = sınırsız
    guest_passes: int
    has_priority: bool

    @computed_field
    @property
    def is_unlimited(self) -> bool:
        return self.monthly_credits is None


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: PlanOut
    remaining_credits: int | None  # None = sınırsız
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime

    @computed_field
    @property
    def is_unlimited(self) -> bool:
        return self.remaining_credits is None


class SubscribeRequest(BaseModel):
    plan_code: PlanType
    card: CardInput


class ChangePlanRequest(BaseModel):
    plan_code: PlanType
    card: CardInput | None = None  # sadece YÜKSELTMEDE gerekli (fark ücreti alınır)


class SubscriptionResult(BaseModel):
    subscription: SubscriptionOut
    payment: PaymentOut | None  # düşürmede ödeme olmaz

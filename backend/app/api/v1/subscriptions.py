from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import ApiResponse, ok
from app.schemas.payment import PaymentOut
from app.schemas.subscription import (
    ChangePlanRequest,
    PlanOut,
    SubscribeRequest,
    SubscriptionOut,
    SubscriptionResult,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Abonelik"])

customer_only = require_roles(UserRole.CUSTOMER)


def _result(sub, payment) -> dict:
    return ok(
        {
            "subscription": SubscriptionOut.model_validate(sub),
            "payment": PaymentOut.model_validate(payment) if payment else None,
        }
    )


@router.get("/plans", response_model=ApiResponse[list[PlanOut]], summary="Paketleri listele (giriş gerekmez)")
def list_plans(db: Session = Depends(get_db)):
    return ok([PlanOut.model_validate(p) for p in SubscriptionService(db).list_plans()])


@router.post(
    "",
    response_model=ApiResponse[SubscriptionResult],
    status_code=status.HTTP_201_CREATED,
    summary="Abonelik başlat (kartla öde)",
)
def subscribe(body: SubscribeRequest, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Ödeme simülasyonu: **4242 4242 4242 4242** her zaman başarılı, **4000 0000 0000 0002** her zaman başarısız.
    Başarılıysa abonelik 30 günlüğüne aktif olur ve paketin kahve hakkı tanımlanır."""
    sub, payment = SubscriptionService(db).subscribe(user, body.plan_code, body.card)
    return _result(sub, payment)


@router.get("/me", response_model=ApiResponse[SubscriptionOut], summary="Aktif aboneliğim")
def get_my_subscription(user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Aktif abonelik yoksa 404 (NO_ACTIVE_SUBSCRIPTION) döner. Dönem bitmişse aylık yenileme burada uygulanır."""
    return ok(SubscriptionOut.model_validate(SubscriptionService(db).require_active(user)))


@router.patch(
    "/me",
    response_model=ApiResponse[SubscriptionResult],
    summary="Paketi yükselt veya düşür",
)
def change_my_plan(body: ChangePlanRequest, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """**Yükseltme:** anında geçerli, fiyat farkı tahsil edilir (kart gerekli), aradaki kahve hakkı eklenir.
    **Düşürme:** anında geçerli, ücret iadesi yok, kalan hak yeni paketin aylık hakkını aşamaz."""
    sub, payment = SubscriptionService(db).change_plan(user, body.plan_code, body.card)
    return _result(sub, payment)


@router.delete("/me", response_model=ApiResponse[SubscriptionOut], summary="Aboneliği iptal et")
def cancel_my_subscription(user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """İptal anında geçerlidir; kalan hak kullanılamaz ve ücret iadesi yoktur."""
    return ok(SubscriptionOut.model_validate(SubscriptionService(db).cancel(user)))

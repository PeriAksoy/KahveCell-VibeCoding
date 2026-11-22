import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models import Order, User
from app.models.enums import STATUS_LABELS, OrderStatus, UserRole
from app.schemas.common import ApiResponse, ok
from app.schemas.order import (
    OrderCreate,
    OrderCreated,
    OrderOut,
    ProductBrief,
    ShopBrief,
    StatusUpdate,
    VerifyQrRequest,
    VerifyQrResult,
)
from app.services import qr_service
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Siparişler"])

customer_only = require_roles(UserRole.CUSTOMER)
shop_owner_only = require_roles(UserRole.SHOP_OWNER)


def _to_out(order: Order, *, with_qr: bool = False) -> OrderOut:
    payload = qr_service.build_payload(order) if with_qr else None
    return OrderOut(
        id=order.id,
        status=order.status,
        status_label=STATUS_LABELS[order.status],
        shop=ShopBrief.model_validate(order.shop),
        product=ProductBrief.model_validate(order.product),
        size=order.size,
        sugar_level=order.sugar_level,
        milk_type=order.milk_type,
        extra_shots=order.extra_shots,
        customer_name=order.user.full_name or "Müşteri",
        is_priority=order.subscription.plan.has_priority,
        created_at=order.created_at,
        updated_at=order.updated_at,
        qr_payload=payload,
        qr_image=qr_service.png_data_uri(payload) if payload else None,
    )


# ---- müşteri ---------------------------------------------------------------------------------

@router.post(
    "",
    response_model=ApiResponse[OrderCreated],
    status_code=status.HTTP_201_CREATED,
    summary="Sipariş ver (abonelikten 1 hak düşer, QR üretilir)",
)
def create_order(body: OrderCreate, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Aktif abonelik ve kalan hak gerekir; yoksa `402` döner (`SUBSCRIPTION_REQUIRED` veya `NO_CREDITS_LEFT`).
    Sınırsız pakette hak düşmez. Cevaptaki `qr_payload` ve `qr_image` müşterinin teslim alırken göstereceği QR koddur."""
    order, remaining = OrderService(db).create(user, body)
    return ok({"order": _to_out(order, with_qr=True), "remaining_credits": remaining})


@router.get("/history", response_model=ApiResponse[list[OrderOut]], summary="Sipariş geçmişim")
def order_history(
    status_filter: OrderStatus | None = Query(None, alias="status", description="Yalnızca bu durumdakiler"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(customer_only),
    db: Session = Depends(get_db),
):
    return ok([_to_out(o) for o in OrderService(db).history(user, status_filter, limit, offset)])


# ---- dükkân sahibi ---------------------------------------------------------------------------

@router.get("/shop", response_model=ApiResponse[list[OrderOut]], summary="Dükkânımın siparişleri (kuyruk)")
def shop_orders(
    status_filter: OrderStatus | None = Query(
        None, alias="status", description="Boşsa yalnızca bitmemiş siparişler (bekleyen, kabul, hazırlanan, hazır)"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    owner: User = Depends(shop_owner_only),
    db: Session = Depends(get_db),
):
    """Kuyruk sırası: öncelikli paket (Unlimited) müşterileri önde, sonra en eski sipariş önde."""
    return ok([_to_out(o) for o in OrderService(db).shop_queue(owner, status_filter, limit, offset)])


@router.post("/verify-qr", response_model=ApiResponse[VerifyQrResult], summary="QR kodu doğrula (durumu değiştirmez)")
def verify_qr(body: VerifyQrRequest, owner: User = Depends(shop_owner_only), db: Session = Depends(get_db)):
    """Dükkân müşterinin QR'ını okutunca burası "evet bu gerçek" der. Sahte veya bozuk QR `400 INVALID_QR`,
    başka dükkânın siparişi `403 WRONG_SHOP` döner. Teslim için ayrıca `PATCH /orders/{id}/status` kullanılır."""
    order, can_deliver, message = OrderService(db).verify_qr(owner, body.qr)
    return ok({"authentic": True, "can_deliver": can_deliver, "message": message, "order": _to_out(order)})


@router.patch("/{order_id}/status", response_model=ApiResponse[OrderOut], summary="Sipariş durumunu güncelle (dükkân)")
def update_order_status(
    order_id: uuid.UUID, body: StatusUpdate, owner: User = Depends(shop_owner_only), db: Session = Depends(get_db)
):
    """Sıra: PENDING → ACCEPTED → PREPARING → READY → COMPLETED. Bekleyen veya kabul edilmiş sipariş
    CANCELLED yapılabilir (hak müşteriye iade edilir). **COMPLETED (teslim) için müşterinin QR içeriğini `qr`
    alanında göndermek zorunludur**; sahte QR ile teslim yapılamaz."""
    order = OrderService(db).update_status(owner, order_id, body.status, body.qr)
    return ok(_to_out(order))


# ---- siparişe özel (sahip müşteri / dükkân / admin) ---------------------------------------------

@router.get("/{order_id}", response_model=ApiResponse[OrderOut], summary="Sipariş detayı (QR ile)")
def get_order(order_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Müşteri kendi siparişini (QR dahil), dükkân sahibi kendi dükkânının siparişini görür. Müşteri bu endpoint'i
    düzenli çağırarak sipariş durumunu takip edebilir."""
    order = OrderService(db).get_for_viewer(user, order_id)
    return ok(_to_out(order, with_qr=order.user_id == user.id))


@router.get(
    "/{order_id}/qr",
    summary="QR kod resmi (PNG)",
    responses={200: {"content": {"image/png": {}}, "description": "QR kodun PNG resmi"}},
    response_class=Response,
)
def get_order_qr(order_id: uuid.UUID, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    order = OrderService(db).get_own(user, order_id)
    return Response(content=qr_service.render_png(qr_service.build_payload(order)), media_type="image/png")


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderOut], summary="Siparişi iptal et (müşteri)")
def cancel_order(order_id: uuid.UUID, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Yalnızca dükkân henüz kabul etmediyse (PENDING) iptal edilir; kahve hakkı iade edilir."""
    return ok(_to_out(OrderService(db).cancel_by_customer(user, order_id)))


@router.post(
    "/{order_id}/reorder",
    response_model=ApiResponse[OrderCreated],
    status_code=status.HTTP_201_CREATED,
    summary="Aynı siparişi tekrar ver",
)
def reorder(order_id: uuid.UUID, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Eski siparişin dükkân, ürün ve özelleştirmeleriyle yeni bir sipariş verir (yeni hak düşer)."""
    order, remaining = OrderService(db).reorder(user, order_id)
    return ok({"order": _to_out(order, with_qr=True), "remaining_credits": remaining})

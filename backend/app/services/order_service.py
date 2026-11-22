import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.timeutil import TURKEY_TZ, as_utc
from app.models import Order, User
from app.models.enums import ORDER_TRANSITIONS, STATUS_LABELS, OrderStatus, SubscriptionStatus, UserRole
from app.models.user import utcnow
from app.repositories.order_repository import OrderRepository
from app.repositories.shop_repository import ShopRepository
from app.schemas.order import OrderCreate, QrPayload
from app.services import qr_service
from app.services.subscription_service import SubscriptionService

ORDER_NOT_FOUND = AppError(404, "ORDER_NOT_FOUND", "Sipariş bulunamadı.")
INVALID_QR = AppError(400, "INVALID_QR", "Sahte veya bozulmuş QR kod. Bu sipariş doğrulanamadı.")


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.shops = ShopRepository(db)
        self.subscriptions = SubscriptionService(db)

    # ---- sipariş verme -----------------------------------------------------------------------

    def create(self, user: User, data: OrderCreate) -> tuple[Order, int | None]:
        """Siparişi oluşturur ve abonelikten 1 hak düşer (sınırsız pakette düşmez). (sipariş, kalan hak) döner."""
        shop = self.shops.get_active(data.shop_id)
        if shop is None:
            raise AppError(404, "SHOP_NOT_FOUND", "Dükkân bulunamadı.")
        product = self.shops.get_product(data.product_id)
        if product is None or product.shop_id != shop.id:
            raise AppError(404, "PRODUCT_NOT_FOUND", "Bu ürün seçtiğiniz dükkânın menüsünde yok.")
        if not product.is_available:
            raise AppError(409, "PRODUCT_UNAVAILABLE", "Bu ürün şu an satışta değil.")

        sub = self.subscriptions.get_active(user)
        if sub is None:
            raise AppError(
                402, "SUBSCRIPTION_REQUIRED", "Sipariş verebilmek için aktif bir aboneliğiniz olmalı. Lütfen bir paket seçin."
            )
        no_credits = AppError(
            402,
            "NO_CREDITS_LEFT",
            "Bu dönemki kahve hakkınız bitti. Hakkınız "
            f"{as_utc(sub.expires_at).astimezone(TURKEY_TZ):%d.%m.%Y} tarihinde yenilenecek; "
            "isterseniz paketinizi yükseltebilirsiniz.",
        )
        if sub.remaining_credits is not None and sub.remaining_credits <= 0:
            raise no_credits

        order = Order(
            user_id=user.id,
            shop_id=shop.id,
            product_id=product.id,
            subscription_id=sub.id,
            size=data.size,
            sugar_level=data.sugar_level,
            milk_type=data.milk_type.value if data.milk_type else None,
            extra_shots=data.extra_shots,
            status=OrderStatus.PENDING,
            created_at=utcnow(),  # QR imzasına girdiği için burada sabitliyoruz
        )
        if sub.remaining_credits is not None and not self.orders.consume_credit(sub.id):
            self.db.rollback()
            raise no_credits  # başka bir istek son hakkı bizden önce aldı
        self.orders.add(order)
        self.db.commit()
        self.db.refresh(sub)
        return self.orders.get(order.id), sub.remaining_credits

    def reorder(self, user: User, order_id: uuid.UUID) -> tuple[Order, int | None]:
        """Eski bir siparişi aynı seçeneklerle tekrar verir (yeni sipariş, yeni hak düşümü)."""
        old = self._get_own(user, order_id)
        return self.create(
            user,
            OrderCreate(
                shop_id=old.shop_id,
                product_id=old.product_id,
                size=old.size,
                sugar_level=old.sugar_level,
                milk_type=old.milk_type,
                extra_shots=old.extra_shots,
            ),
        )

    # ---- görüntüleme -------------------------------------------------------------------------

    def history(self, user: User, status: OrderStatus | None, limit: int, offset: int) -> list[Order]:
        return self.orders.list_for_customer(user.id, status, limit, offset)

    def shop_queue(self, owner: User, status: OrderStatus | None, limit: int, offset: int) -> list[Order]:
        return self.orders.list_for_owner(owner.id, status, limit, offset)

    def get_for_viewer(self, user: User, order_id: uuid.UUID) -> Order:
        """Siparişi yalnızca sahibi (müşteri), dükkânın sahibi veya admin görebilir. Diğerleri 'bulunamadı' alır."""
        order = self.orders.get(order_id)
        if order is None:
            raise ORDER_NOT_FOUND
        allowed = user.role is UserRole.ADMIN or order.user_id == user.id or order.shop.owner_id == user.id
        if not allowed:
            raise ORDER_NOT_FOUND
        return order

    def get_own(self, user: User, order_id: uuid.UUID) -> Order:
        return self._get_own(user, order_id)

    # ---- durum güncelleme --------------------------------------------------------------------

    def update_status(self, owner: User, order_id: uuid.UUID, target: OrderStatus, qr: QrPayload | None) -> Order:
        order = self._get_for_owner(owner, order_id)
        if target not in ORDER_TRANSITIONS[order.status]:
            allowed = ", ".join(STATUS_LABELS[s] for s in ORDER_TRANSITIONS[order.status]) or "yok"
            raise AppError(
                409,
                "INVALID_TRANSITION",
                f"Sipariş '{STATUS_LABELS[order.status]}' durumundan '{STATUS_LABELS[target]}' durumuna geçemez. "
                f"Geçilebilecek durumlar: {allowed}.",
            )
        if target is OrderStatus.COMPLETED:
            # Teslim, müşterinin QR'ı doğrulanmadan yapılamaz.
            if qr is None:
                raise AppError(400, "QR_REQUIRED", "Teslim etmek için müşterinin QR kodu gerekli (qr alanı).")
            if self._authentic_order(qr).id != order.id:
                raise AppError(400, "QR_MISMATCH", "Bu QR kod başka bir siparişe ait.")
        if target is OrderStatus.CANCELLED:
            self._refund_credit(order)
        order.status = target
        self.db.commit()
        return self.orders.get(order.id)

    def cancel_by_customer(self, user: User, order_id: uuid.UUID) -> Order:
        order = self._get_own(user, order_id)
        if order.status is not OrderStatus.PENDING:
            raise AppError(
                409, "CANNOT_CANCEL", "Sipariş dükkân tarafından kabul edildikten sonra iptal edilemez."
            )
        self._refund_credit(order)
        order.status = OrderStatus.CANCELLED
        self.db.commit()
        return self.orders.get(order.id)

    # ---- QR doğrulama ------------------------------------------------------------------------

    def verify_qr(self, owner: User, payload: QrPayload) -> tuple[Order, bool, str]:
        """Dükkânın QR okutması: (sipariş, teslim edilebilir mi, mesaj). Durumu DEĞİŞTİRMEZ.
        Sahte QR 400 (INVALID_QR), başka dükkânın siparişi 403 (WRONG_SHOP) verir."""
        order = self._authentic_order(payload)
        if order.shop.owner_id != owner.id:
            raise AppError(403, "WRONG_SHOP", "Bu sipariş sizin dükkânınıza ait değil.")
        if order.status is OrderStatus.READY:
            return order, True, "QR kod gerçek. Sipariş hazır, teslim edebilirsiniz."
        if order.status is OrderStatus.COMPLETED:
            return order, False, "QR kod gerçek ancak bu sipariş zaten teslim edilmiş."
        if order.status is OrderStatus.CANCELLED:
            return order, False, "QR kod gerçek ancak sipariş iptal edilmiş."
        return order, False, f"QR kod gerçek ancak sipariş henüz hazır değil (durum: {STATUS_LABELS[order.status]})."

    # ---- yardımcılar -------------------------------------------------------------------------

    def _authentic_order(self, payload: QrPayload) -> Order:
        """İmzayı ve içeriğin veritabanıyla uyumunu kontrol eder; sahteyse INVALID_QR fırlatır."""
        if not qr_service.is_signature_valid(payload):
            raise INVALID_QR
        order = self.orders.get(payload.order_id)
        if order is None or not qr_service.matches_order(payload, order):
            raise INVALID_QR
        return order

    def _get_own(self, user: User, order_id: uuid.UUID) -> Order:
        order = self.orders.get(order_id)
        if order is None or order.user_id != user.id:
            raise ORDER_NOT_FOUND
        return order

    def _get_for_owner(self, owner: User, order_id: uuid.UUID) -> Order:
        order = self.orders.get(order_id)
        if order is None or order.shop.owner_id != owner.id:
            raise ORDER_NOT_FOUND
        return order

    def _refund_credit(self, order: Order) -> None:
        """İptalde hak iade edilir (sınırsız pakette hak zaten düşmemişti; aylık hakkı da aşamaz)."""
        sub = order.subscription
        if sub.status is SubscriptionStatus.ACTIVE and sub.remaining_credits is not None:
            restored = sub.remaining_credits + 1
            cap = sub.plan.monthly_credits
            sub.remaining_credits = restored if cap is None else min(restored, cap)

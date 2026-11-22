from datetime import timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.timeutil import as_utc
from app.models import Payment, Plan, Subscription, User
from app.models.enums import PaymentStatus, PlanType, SubscriptionStatus
from app.models.user import utcnow
from app.repositories.payment_repository import PaymentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.payment import CardInput
from app.services.payment_service import PaymentService

PERIOD = timedelta(days=30)  # bir abonelik dönemi
CENT = Decimal("0.01")

NO_ACTIVE = AppError(404, "NO_ACTIVE_SUBSCRIPTION", "Aktif bir aboneliğiniz yok.")


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.subs = SubscriptionRepository(db)
        self.payments = PaymentRepository(db)
        self.payment_service = PaymentService(db)

    # ---- okuma -------------------------------------------------------------------------------

    def list_plans(self) -> list[Plan]:
        return self.subs.list_plans()

    def get_active(self, user: User) -> Subscription | None:
        """Aktif aboneliği döner. Dönem bitmişse önce aylık yenilemeyi uygular."""
        sub = self.subs.get_active_for_user(user.id)
        if sub is not None and as_utc(sub.expires_at) <= utcnow():
            self._renew(user, sub)
        return sub

    def require_active(self, user: User) -> Subscription:
        sub = self.get_active(user)
        if sub is None:
            raise NO_ACTIVE
        return sub

    # ---- işlemler ----------------------------------------------------------------------------

    def subscribe(self, user: User, plan_code: PlanType, card: CardInput) -> tuple[Subscription, Payment]:
        if self.get_active(user) is not None:
            raise AppError(
                409, "ALREADY_SUBSCRIBED", "Zaten aktif bir aboneliğiniz var. Paket değiştirmek için PATCH kullanın."
            )
        plan = self._get_plan(plan_code)

        payment, failure = self.payment_service.charge(user, plan, plan.monthly_price, card)
        if failure:
            self._commit_failed_payment(payment, failure)

        now = utcnow()
        sub = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            remaining_credits=plan.monthly_credits,  # None = sınırsız
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=now + PERIOD,
        )
        try:
            self.subs.add(sub)
            payment.subscription_id = sub.id
            self.db.commit()
        except IntegrityError:  # aynı anda ikinci istek: veritabanı tek aktif aboneliğe izin vermez
            self.db.rollback()
            raise AppError(409, "ALREADY_SUBSCRIBED", "Zaten aktif bir aboneliğiniz var.")
        self.db.refresh(sub)
        return sub, payment

    def change_plan(self, user: User, plan_code: PlanType, card: CardInput | None) -> tuple[Subscription, Payment | None]:
        sub = self.require_active(user)
        current = sub.plan
        target = self._get_plan(plan_code)
        if target.id == current.id:
            raise AppError(409, "SAME_PLAN", "Zaten bu paketi kullanıyorsunuz.")

        payment = None
        if target.monthly_price > current.monthly_price:
            # YÜKSELTME: anında geçerli. Fiyat farkı tahsil edilir, aradaki kahve hakkı hemen eklenir.
            if card is None:
                raise AppError(400, "CARD_REQUIRED", "Paketi yükseltmek için kart bilgisi gerekli.")
            difference = (target.monthly_price - current.monthly_price).quantize(CENT)
            payment, failure = self.payment_service.charge(user, target, difference, card)
            if failure:
                self._commit_failed_payment(payment, failure)
            if target.monthly_credits is None:
                sub.remaining_credits = None
            else:
                extra = target.monthly_credits - (current.monthly_credits or 0)
                sub.remaining_credits = (sub.remaining_credits or 0) + extra
            payment.subscription_id = sub.id
        else:
            # DÜŞÜRME: anında geçerli, ücret iadesi yok. Kalan hak yeni paketin aylık hakkını aşamaz.
            cap = target.monthly_credits  # düşürme hedefi hiçbir zaman sınırsız olmaz
            sub.remaining_credits = cap if sub.remaining_credits is None else min(sub.remaining_credits, cap)

        sub.plan = target
        self.db.commit()
        self.db.refresh(sub)
        return sub, payment

    def cancel(self, user: User) -> Subscription:
        """İptal anında geçerlidir (kalan hak kullanılamaz, ücret iadesi yok)."""
        sub = self.require_active(user)
        sub.status = SubscriptionStatus.CANCELLED
        self.db.commit()
        self.db.refresh(sub)
        return sub

    # ---- yardımcılar -------------------------------------------------------------------------

    def _get_plan(self, code: PlanType) -> Plan:
        plan = self.subs.get_plan_by_code(code)
        if plan is None:
            raise AppError(404, "PLAN_NOT_FOUND", "Paket bulunamadı.")
        return plan

    def _commit_failed_payment(self, payment: Payment, message: str) -> None:
        """Başarısız deneme de ödeme geçmişine yazılır; sonra hata fırlatılır."""
        self.db.commit()
        raise AppError(402, "PAYMENT_FAILED", message)

    def _renew(self, user: User, sub: Subscription) -> None:
        """Aylık yenileme (simülasyon): önceki başarılı kartla yeni ödeme alınır, hak yenilenir, dönem 30 gün uzar.
        Uzun süre girilmediyse tek yenileme yapılır; yeni dönem yenilemenin yapıldığı andan başlar."""
        last = self.payments.last_successful(user.id)
        payment = self.payment_service.record_renewal(user, sub.plan, last.card_last4 if last else "0000")
        payment.subscription_id = sub.id
        now = utcnow()
        sub.remaining_credits = sub.plan.monthly_credits
        sub.started_at = now
        sub.expires_at = now + PERIOD
        self.db.commit()
        self.db.refresh(sub)

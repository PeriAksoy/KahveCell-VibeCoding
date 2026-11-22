"""Sahte ödeme sağlayıcısı (simülasyon). Gerçek bir ödeme API'si çağrılmaz."""
import logging
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Payment, Plan, User
from app.models.enums import PaymentStatus
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import CardInput

logger = logging.getLogger("kahvecell")

CARD_ALWAYS_SUCCEEDS = "4242424242424242"
CARD_ALWAYS_DECLINED = "4000000000000002"

DECLINED_MESSAGE = "Kartınız reddedildi (simülasyon: bakiye yetersiz)."
UNSUPPORTED_MESSAGE = "Bu simülasyonda yalnızca test kartları kabul edilir (4242 4242 4242 4242)."


class PaymentService:
    def __init__(self, db: Session):
        self.payments = PaymentRepository(db)

    def charge(self, user: User, plan: Plan, amount: Decimal, card: CardInput) -> tuple[Payment, str | None]:
        """Kartı 'çeker' ve ödeme kaydını oluşturur (başarısız denemeler dahil).
        (ödeme, hata_mesajı) döner; başarılıysa hata_mesajı None'dır. Commit çağıran tarafta yapılır."""
        number = card.card_number
        if number == CARD_ALWAYS_SUCCEEDS:
            status, message = PaymentStatus.SUCCESS, None
        elif number == CARD_ALWAYS_DECLINED:
            status, message = PaymentStatus.FAILED, DECLINED_MESSAGE
        else:
            status, message = PaymentStatus.FAILED, UNSUPPORTED_MESSAGE

        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            transaction_id=f"TXN-{uuid.uuid4().hex[:16].upper()}",
            amount=amount,
            status=status,
            card_last4=number[-4:],  # kartın tamamı ASLA saklanmaz ve loglanmaz
        )
        self.payments.add(payment)
        logger.info("Ödeme %s tx=%s tutar=%s", status.value, payment.transaction_id, amount)
        return payment, message

    def record_renewal(self, user: User, plan: Plan, card_last4: str) -> Payment:
        """Aylık otomatik yenileme: önceki başarılı kartla yeni bir ödeme kaydı (simülasyon, her zaman başarılı)."""
        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            transaction_id=f"RNW-{uuid.uuid4().hex[:16].upper()}",
            amount=plan.monthly_price,
            status=PaymentStatus.SUCCESS,
            card_last4=card_last4,
        )
        self.payments.add(payment)
        return payment

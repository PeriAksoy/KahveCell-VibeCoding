import hmac
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.timeutil import as_utc
from app.models import User
from app.models.user import utcnow
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("kahvecell")

INVALID_LOGIN = AppError(401, "INVALID_OTP", "Telefon numarası veya doğrulama kodu hatalı.")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def request_otp(self, phone_number: str) -> tuple[User, bool]:
        """Kayıtlı değilse kullanıcıyı oluşturur (hep MÜŞTERİ rolüyle), sonra OTP 'gönderir'."""
        user = self.users.get_by_phone(phone_number)
        is_new = user is None
        if is_new:
            user = self.users.create(phone_number)
            self.db.commit()
        # Gerçek SMS yok: kod sabit (ayarlardaki OTP_CODE). Gerçek sistemde burada SMS sağlayıcısı çağrılırdı.
        logger.info("OTP gönderildi (simülasyon) phone=***%s", phone_number[-4:])
        return user, is_new

    def request_login_otp(self, phone_number: str) -> None:
        """Giriş için OTP 'gönderir'. Kayıtlı olmayan numara için yeni kullanıcı OLUŞTURMAZ, hata verir."""
        if self.users.get_by_phone(phone_number) is None:
            raise AppError(404, "USER_NOT_FOUND", "Bu numara kayıtlı değil. Lütfen önce kayıt olun.")
        logger.info("OTP gönderildi (simülasyon) phone=***%s", phone_number[-4:])

    def verify_otp(self, phone_number: str, code: str) -> tuple[User, dict]:
        user = self.users.get_by_phone(phone_number)
        code_ok = hmac.compare_digest(code.encode(), settings.otp_code.encode())
        if user is None or not code_ok:
            # Numara yok mu kod mu yanlış, bilerek ayırt ettirmiyoruz.
            raise INVALID_LOGIN
        return user, self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token, "refresh")
        stored = self.tokens.get(payload.get("jti", ""))
        if stored is None or as_utc(stored.expires_at) <= utcnow():
            raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
        if stored.revoked_at is not None:
            # İptal edilmiş bilet tekrar kullanıldı: çalınmış olabilir, kullanıcının bütün oturumlarını kapat.
            self.tokens.revoke_all_for_user(stored.user_id)
            self.db.commit()
            raise AppError(401, "TOKEN_REVOKED", "Oturum sonlandırılmış, lütfen yeniden giriş yapın.")
        user = self.users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None:
            raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
        self.tokens.revoke(stored)  # her yenilemede eski bilet iptal, yenisi verilir (rotation)
        return self._issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, "refresh")
        stored = self.tokens.get(payload.get("jti", ""))
        if stored is not None and stored.revoked_at is None:
            self.tokens.revoke(stored)
            self.db.commit()

    def _issue_tokens(self, user: User) -> dict:
        access = create_access_token(user.id)
        refresh, jti, expires_at = create_refresh_token(user.id)
        self.tokens.add(jti, user.id, expires_at)
        self.db.commit()
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_minutes * 60,
        }

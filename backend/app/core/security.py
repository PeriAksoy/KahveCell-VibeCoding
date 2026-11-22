"""JWT üretme ve doğrulama."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.exceptions import AppError


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """(token, jti, bitiş zamanı) döner. jti, tokenın veritabanındaki kimliğidir (iptal edebilmek için)."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.refresh_token_days)
    jti = str(uuid.uuid4())
    payload = {"sub": str(user_id), "type": "refresh", "jti": jti, "iat": now, "exp": expires_at}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str, expected_type: str) -> dict:
    """Tokenı doğrular. Süresi dolmuş, bozuk veya yanlış türde ise AppError(401) fırlatır."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "Oturum süresi doldu, lütfen yeniden giriş yapın.")
    except jwt.InvalidTokenError:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
    if payload["type"] != expected_type:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
    return payload

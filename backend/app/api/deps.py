"""Endpoint'lerin ortak bağımlılıkları: 'giriş yapmış kullanıcı' ve 'rol kontrolü'."""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.models import User
from app.models.enums import UserRole

# Swagger'da sağ üstte "Authorize" butonunu çıkarır.
bearer_scheme = HTTPBearer(auto_error=False, description="verify-otp'tan dönen access_token (başına Bearer yazma)")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError(401, "NOT_AUTHENTICATED", "Bu işlem için giriş yapmanız gerekiyor.")
    payload = decode_token(credentials.credentials, "access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi.")
    return user  # rol bilgisi tokendan değil, her seferinde veritabanından okunur


def require_roles(*roles: UserRole):
    """Kullanım: Depends(require_roles(UserRole.ADMIN)) -> başka rol 403 alır."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(403, "FORBIDDEN", "Bu işlem için yetkiniz yok.")
        return user

    return checker

import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import RefreshToken
from app.models.user import utcnow


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, jti: str, user_id: uuid.UUID, expires_at: datetime) -> None:
        self.db.add(RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at))

    def get(self, jti: str) -> RefreshToken | None:
        return self.db.get(RefreshToken, jti)

    def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = utcnow()

    def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )

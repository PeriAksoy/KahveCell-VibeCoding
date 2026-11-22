import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.enums import UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_phone(self, phone_number: str) -> User | None:
        return self.db.scalar(select(User).where(User.phone_number == phone_number))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def list(self, limit: int, offset: int) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at).limit(limit).offset(offset)))

    def create(self, phone_number: str, role: UserRole = UserRole.CUSTOMER) -> User:
        user = User(phone_number=phone_number, role=role)
        self.db.add(user)
        self.db.flush()
        return user

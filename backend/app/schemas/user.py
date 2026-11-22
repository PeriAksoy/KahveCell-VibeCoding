import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models.enums import UserRole

ShortText = Annotated[str, Field(min_length=1, max_length=50)]


class Preferences(BaseModel):
    coffees: list[ShortText] = Field(default_factory=list, max_length=20)
    allergens: list[ShortText] = Field(default_factory=list, max_length=20)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_number: str
    full_name: str | None
    email: str | None
    role: UserRole
    preferences: dict | None
    created_at: datetime

    @computed_field
    @property
    def profile_complete(self) -> bool:
        """İlk girişten sonra ad soyad girilmediyse arayüz 'profil tamamlama' ekranını gösterir."""
        return bool(self.full_name)


class UserUpdate(BaseModel):
    """Sadece gönderilen alanlar güncellenir."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    preferences: Preferences | None = None

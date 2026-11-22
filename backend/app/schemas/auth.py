from pydantic import BaseModel, Field, field_validator

from app.core.phone import normalize_phone
from app.schemas.user import UserOut


class PhoneRequest(BaseModel):
    phone_number: str = Field(examples=["5551234567"])

    @field_validator("phone_number")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_phone(value)


class RegisterResult(BaseModel):
    phone_number: str
    is_new_user: bool
    message: str


class VerifyOtpRequest(PhoneRequest):
    code: str = Field(min_length=4, max_length=6, examples=["1234"])


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="access_token kaç saniye geçerli")


class LoginResult(TokenPair):
    user: UserOut

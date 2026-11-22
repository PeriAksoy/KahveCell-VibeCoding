from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, PlainSerializer

T = TypeVar("T")

# Para tutarları JSON'da "89.99" (metin) yerine 89.99 (sayı) olarak çıksın.
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class ApiError(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Bütün cevaplar bu zarfın içinde döner: { success, data, error }."""

    success: bool = True
    data: T | None = None
    error: ApiError | None = None


def ok(data: Any = None) -> dict:
    return {"success": True, "data": data, "error": None}

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories.payment_repository import PaymentRepository
from app.schemas.common import ApiResponse, ok
from app.schemas.payment import PaymentOut

router = APIRouter(prefix="/payments", tags=["Ödemeler"])


@router.get("/me", response_model=ApiResponse[list[PaymentOut]], summary="Ödeme geçmişim")
def my_payments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Başarılı ve başarısız bütün ödeme denemeleri, en yenisi başta."""
    return ok([PaymentOut.model_validate(p) for p in PaymentRepository(db).list_for_user(user.id, limit, offset)])

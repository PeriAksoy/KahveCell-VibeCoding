from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import User
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import ApiResponse, ok
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Kullanıcılar"])


@router.get("/me", response_model=ApiResponse[UserOut], summary="Kendi profilim")
def get_me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.patch("/me", response_model=ApiResponse[UserOut], summary="Profilimi güncelle / tamamla")
def update_me(body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ad soyad, e-posta ve kahve tercihleri/alerjenler. Yalnızca gönderdiğin alanlar değişir."""
    changes = body.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] is not None:
        existing = UserRepository(db).get_by_email(changes["email"])
        if existing is not None and existing.id != user.id:
            raise AppError(409, "EMAIL_TAKEN", "Bu e-posta adresi başka bir hesapta kullanılıyor.")
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user))


@router.get(
    "",
    response_model=ApiResponse[list[UserOut]],
    summary="Kullanıcı listesi (yalnızca ADMIN)",
)
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return ok([UserOut.model_validate(u) for u in UserRepository(db).list(limit, offset)])

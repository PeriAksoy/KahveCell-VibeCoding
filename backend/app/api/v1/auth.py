from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    LoginResult,
    PhoneRequest,
    RefreshRequest,
    RegisterResult,
    TokenPair,
    VerifyOtpRequest,
)
from app.schemas.common import ApiResponse, ok
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Kimlik doğrulama"])


@router.post(
    "/register",
    response_model=ApiResponse[RegisterResult],
    summary="Kayıt ol / giriş başlat (OTP gönder)",
)
def register(body: PhoneRequest, db: Session = Depends(get_db)):
    """Telefon numarasıyla kayıt olur. Numara zaten kayıtlıysa yeni kayıt açmaz, yalnızca OTP gönderir
    (yani giriş için de aynı endpoint kullanılır). SMS simülasyondur: kod her zaman **1234**."""
    _, is_new = AuthService(db).request_otp(body.phone_number)
    return ok(
        {
            "phone_number": body.phone_number,
            "is_new_user": is_new,
            "message": "Doğrulama kodu gönderildi (simülasyon: 1234).",
        }
    )


@router.post(
    "/login",
    response_model=ApiResponse[RegisterResult],
    summary="Giriş yap (kayıtlı numaraya OTP gönder)",
)
def login(body: PhoneRequest, db: Session = Depends(get_db)):
    """Yalnızca KAYITLI numaralar için OTP gönderir; kayıtlı değilse `404 USER_NOT_FOUND` döner ve hesap açmaz.
    Kodu doğrulamak için `verify-otp` kullanılır."""
    AuthService(db).request_login_otp(body.phone_number)
    return ok(
        {
            "phone_number": body.phone_number,
            "is_new_user": False,
            "message": "Doğrulama kodu gönderildi (simülasyon: 1234).",
        }
    )


@router.post(
    "/verify-otp",
    response_model=ApiResponse[LoginResult],
    summary="OTP doğrula ve giriş yap",
)
def verify_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Kod doğruysa access_token (kısa ömürlü) ve refresh_token (uzun ömürlü) döner.
    Böylece kullanıcıdan her seferinde yeniden kod istenmez."""
    user, tokens = AuthService(db).verify_otp(body.phone_number, body.code)
    return ok({**tokens, "user": UserOut.model_validate(user)})


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenPair],
    summary="Oturumu yenile",
)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """access_token süresi dolunca refresh_token ile yeni bir çift alınır. Eski refresh_token iptal olur."""
    return ok(AuthService(db).refresh(body.refresh_token))


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="Çıkış yap",
)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    """refresh_token'ı iptal eder; bu oturum bir daha yenilenemez."""
    AuthService(db).logout(body.refresh_token)
    return ok()

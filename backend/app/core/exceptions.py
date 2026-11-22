"""Standart hata formatı: her hata { success: false, data: null, error: {code, message, details} } döner."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("kahvecell")


class AppError(Exception):
    """Bilinen, kullanıcıya gösterilebilir iş hatası."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def _body(code: str, message: str, details=None) -> dict:
    return {"success": False, "data": None, "error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]),
                "message": err["msg"].removeprefix("Value error, "),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("VALIDATION_ERROR", "Gönderilen bilgilerde hata var.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content=_body(f"HTTP_{exc.status_code}", str(exc.detail)))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception):
        logger.exception("Beklenmeyen hata", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_body("INTERNAL_ERROR", "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."),
        )

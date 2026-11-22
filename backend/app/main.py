import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  (tabloların tanınması için)
from app.api.v1.router import api_router
from app.core.config import DEV_SECRET_KEY, settings
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kahvecell")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Uygulama açılırken eksik tablolar varsa oluşturur; olanlara dokunmaz.
    Base.metadata.create_all(bind=engine)
    if settings.secret_key == DEV_SECRET_KEY:
        logger.warning("SECRET_KEY varsayılan geliştirme değerinde. Canlıda .env ile değiştir!")
    yield


app = FastAPI(title="KahveCell API", version="0.1.0", lifespan=lifespan)
register_exception_handlers(app)

# React (Vite) geliştirme sunucusunun backend'e istek atabilmesi için izin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Sistem"])
def root():
    return {"success": True, "data": {"message": "KahveCell backend çalışıyor ☕"}, "error": None}

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/

DEV_SECRET_KEY = "gelistirme-icin-gecici-anahtar-canlida-MUTLAKA-degistir"


class Settings(BaseSettings):
    # Ayarlar .env dosyasından okunur; yoksa aşağıdaki varsayılanlar kullanılır.
    database_url: str = f"sqlite:///{BASE_DIR / 'kahvecell.db'}"

    # JWT (giriş bileti) ayarları
    secret_key: str = DEV_SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30  # kısa ömürlü bilet
    refresh_token_days: int = 7  # uzun ömürlü yenileme bileti

    # SMS simülasyonu: gerçek SMS yok, kod sabit.
    otp_code: str = "1234"

    # Frontend'in backend'e istek atmasına izin verilen adresler (virgülle ayrılır).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()

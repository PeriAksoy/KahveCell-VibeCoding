"""QR kod üretimi ve sahtecilik kontrolü.

QR içeriği (case 13.2): { order_id, user_id, shop_id, created_at, signature }
'signature', bu dört alanın sunucudaki gizli anahtarla alınmış HMAC-SHA256 imzasıdır. Anahtarı yalnızca
sunucu bilir; bu yüzden bir alan değiştirilirse veya sıfırdan uydurulursa imza tutmaz.
"""
import base64
import hashlib
import hmac
import io
import json
import uuid
from datetime import datetime

import qrcode

from app.core.config import settings
from app.core.timeutil import as_utc
from app.models import Order
from app.schemas.order import QrPayload


def _key() -> bytes:
    # Oturum biletleriyle aynı anahtarı doğrudan kullanmamak için ayrı bir alt anahtar türetiliyor.
    return hashlib.sha256(f"qr:{settings.secret_key}".encode()).digest()


def format_created_at(value: datetime) -> str:
    """ISO8601, milisaniye hassasiyetinde ve UTC: 2026-11-22T14:30:00.123Z"""
    return as_utc(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sign(order_id: uuid.UUID, user_id: uuid.UUID, shop_id: uuid.UUID, created_at: str) -> str:
    message = f"{order_id}|{user_id}|{shop_id}|{created_at}".encode()
    return hmac.new(_key(), message, hashlib.sha256).hexdigest()


def build_payload(order: Order) -> QrPayload:
    created_at = format_created_at(order.created_at)
    return QrPayload(
        order_id=order.id,
        user_id=order.user_id,
        shop_id=order.shop_id,
        created_at=created_at,
        signature=_sign(order.id, order.user_id, order.shop_id, created_at),
    )


def is_signature_valid(payload: QrPayload) -> bool:
    expected = _sign(payload.order_id, payload.user_id, payload.shop_id, payload.created_at)
    return hmac.compare_digest(expected, payload.signature.lower())


def matches_order(payload: QrPayload, order: Order) -> bool:
    """İmza geçerli olsa bile QR'ın içeriği veritabanındaki siparişle birebir uyuşmalı."""
    return (
        payload.order_id == order.id
        and payload.user_id == order.user_id
        and payload.shop_id == order.shop_id
        and payload.created_at == format_created_at(order.created_at)
    )


def to_content(payload: QrPayload) -> str:
    """QR koda yazılan metin: case'deki JSON."""
    return json.dumps(payload.model_dump(mode="json"), separators=(",", ":"), ensure_ascii=False)


def render_png(payload: QrPayload) -> bytes:
    # Hata düzeltme seviyesi L: içerik sabit (case'deki JSON), seviye düşünce QR daha az kareden oluşur ve
    # her kare büyür; kamera ile okumak kolaylaşır. Ekrandan okutulduğu için fiziksel hasar riski yoktur.
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=3)
    qr.add_data(to_content(payload))
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def png_data_uri(payload: QrPayload) -> str:
    return "data:image/png;base64," + base64.b64encode(render_png(payload)).decode()

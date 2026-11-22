import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, ok
from app.schemas.shop import ProductOut, ShopDetailOut, ShopListResult, ShopOut
from app.services.shop_service import ShopHit, ShopService, ShopSort

router = APIRouter(prefix="/shops", tags=["Dükkânlar"])


def _to_out(hit: ShopHit) -> ShopOut:
    s = hit.shop
    return ShopOut(
        id=s.id, name=s.name, address=s.address, latitude=s.latitude, longitude=s.longitude,
        opens_at=s.opens_at, closes_at=s.closes_at, is_open=hit.is_open, rating=s.rating,
        image_url=s.image_url, distance_km=hit.distance_km,
    )


@router.get(
    "",
    response_model=ApiResponse[ShopListResult],
    summary="Dükkânları listele, ara, yakındakileri getir (giriş gerekmez)",
)
def list_shops(
    lat: float | None = Query(None, ge=-90, le=90, description="Kullanıcının enlemi. lng ile BİRLİKTE gönderilir."),
    lng: float | None = Query(None, ge=-180, le=180, description="Kullanıcının boylamı. lat ile birlikte gönderilir."),
    radius: float | None = Query(None, gt=0, le=500, description="Kilometre cinsinden yarıçap (lat/lng gerekir)."),
    q: str | None = Query(None, min_length=1, max_length=100, description="İsim veya adreste arama (Türkçe karakter ve büyük/küçük harf fark etmez)."),
    min_rating: float | None = Query(None, ge=0, le=5, description="En düşük puan."),
    is_open: bool | None = Query(None, description="true: şu an açık olanlar, false: kapalı olanlar."),
    sort: ShopSort | None = Query(None, description="distance | rating | name. Boşsa: konum varsa distance, yoksa name."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Hiçbir filtre vermezsen bütün dükkânlar gelir. `lat` ve `lng` verirsen her dükkânın `distance_km`
    değeri hesaplanır ve en yakın olan başa gelir. Filtreler birlikte kullanılabilir."""
    hits, total = ShopService(db).search(
        lat=lat, lng=lng, radius_km=radius, q=q, min_rating=min_rating,
        is_open=is_open, sort=sort, limit=limit, offset=offset,
    )
    return ok({"items": [_to_out(h) for h in hits], "total": total})


@router.get("/{shop_id}", response_model=ApiResponse[ShopDetailOut], summary="Dükkân detayı ve menüsü")
def get_shop(
    shop_id: uuid.UUID,
    lat: float | None = Query(None, ge=-90, le=90, description="Mesafe için (isteğe bağlı)."),
    lng: float | None = Query(None, ge=-180, le=180, description="Mesafe için (isteğe bağlı)."),
    db: Session = Depends(get_db),
):
    hit, products = ShopService(db).get_detail(shop_id, lat, lng)
    return ok({**_to_out(hit).model_dump(), "menu": [ProductOut.model_validate(p) for p in products]})


@router.get("/{shop_id}/menu", response_model=ApiResponse[list[ProductOut]], summary="Yalnızca menü")
def get_menu(shop_id: uuid.UUID, db: Session = Depends(get_db)):
    """Satışta olmayan ürünler de listelenir, `is_available: false` ile işaretlenir."""
    return ok([ProductOut.model_validate(p) for p in ShopService(db).get_menu(shop_id)])

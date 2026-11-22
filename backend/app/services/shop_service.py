import enum
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.geo import bounding_box, haversine_km
from app.core.text import fold
from app.core.timeutil import is_open_at, turkey_now
from app.models import Product, Shop
from app.repositories.shop_repository import ShopRepository


class ShopSort(str, enum.Enum):
    DISTANCE = "distance"  # en yakın önce (konum gerekir)
    RATING = "rating"  # en yüksek puan önce
    NAME = "name"  # alfabetik


@dataclass
class ShopHit:
    shop: Shop
    distance_km: float | None
    is_open: bool


class ShopService:
    def __init__(self, db: Session):
        self.shops = ShopRepository(db)

    def search(
        self,
        *,
        lat: float | None,
        lng: float | None,
        radius_km: float | None,
        q: str | None,
        min_rating: float | None,
        is_open: bool | None,
        sort: ShopSort | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ShopHit], int]:
        self._check_location(lat, lng)
        has_location = lat is not None
        if radius_km is not None and not has_location:
            raise AppError(400, "LOCATION_REQUIRED", "radius kullanmak için lat ve lng de gönderilmeli.")
        sort = sort or (ShopSort.DISTANCE if has_location else ShopSort.NAME)
        if sort is ShopSort.DISTANCE and not has_location:
            raise AppError(400, "LOCATION_REQUIRED", "Mesafeye göre sıralamak için lat ve lng gönderilmeli.")

        box = bounding_box(lat, lng, radius_km) if radius_km is not None else None
        now = turkey_now().time()
        needle = fold(q.strip()) if q else None

        hits: list[ShopHit] = []
        for shop in self.shops.list_active(box):
            if needle and needle not in fold(shop.name) and needle not in fold(shop.address):
                continue
            if min_rating is not None and shop.rating < min_rating:
                continue
            opened = is_open_at(shop.opens_at, shop.closes_at, now)
            if is_open is not None and opened != is_open:
                continue
            distance = None
            if has_location:
                distance = haversine_km(lat, lng, shop.latitude, shop.longitude)
                if radius_km is not None and distance > radius_km:
                    continue
            hits.append(ShopHit(shop, round(distance, 2) if distance is not None else None, opened))

        if sort is ShopSort.DISTANCE:
            hits.sort(key=lambda h: (h.distance_km, fold(h.shop.name)))
        elif sort is ShopSort.RATING:
            hits.sort(key=lambda h: (-h.shop.rating, fold(h.shop.name)))
        else:
            hits.sort(key=lambda h: fold(h.shop.name))
        return hits[offset : offset + limit], len(hits)

    def get_detail(self, shop_id: uuid.UUID, lat: float | None, lng: float | None) -> tuple[ShopHit, list[Product]]:
        self._check_location(lat, lng)
        shop = self._get_or_404(shop_id)
        distance = None
        if lat is not None:
            distance = round(haversine_km(lat, lng, shop.latitude, shop.longitude), 2)
        opened = is_open_at(shop.opens_at, shop.closes_at, turkey_now().time())
        return ShopHit(shop, distance, opened), self.shops.list_products(shop.id)

    def get_menu(self, shop_id: uuid.UUID) -> list[Product]:
        return self.shops.list_products(self._get_or_404(shop_id).id)

    def _get_or_404(self, shop_id: uuid.UUID) -> Shop:
        shop = self.shops.get_active(shop_id)
        if shop is None:
            raise AppError(404, "SHOP_NOT_FOUND", "Dükkân bulunamadı.")
        return shop

    @staticmethod
    def _check_location(lat: float | None, lng: float | None) -> None:
        if (lat is None) != (lng is None):
            raise AppError(400, "LOCATION_INCOMPLETE", "Konum için lat ve lng birlikte gönderilmeli.")

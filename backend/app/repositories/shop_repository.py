import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, Shop


class ShopRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active(self, box: tuple[float, float, float | None, float | None] | None = None) -> list[Shop]:
        """Aktif dükkânlar. 'box' verilirse (min_lat, max_lat, min_lng, max_lng) indeksli ön eleme yapılır."""
        query = select(Shop).where(Shop.is_active.is_(True))
        if box is not None:
            min_lat, max_lat, min_lng, max_lng = box
            query = query.where(Shop.latitude.between(min_lat, max_lat))
            if min_lng is not None:
                query = query.where(Shop.longitude.between(min_lng, max_lng))
        return list(self.db.scalars(query))

    def get_active(self, shop_id: uuid.UUID) -> Shop | None:
        return self.db.scalar(select(Shop).where(Shop.id == shop_id, Shop.is_active.is_(True)))

    def get_product(self, product_id: uuid.UUID) -> Product | None:
        return self.db.get(Product, product_id)

    def list_products(self, shop_id: uuid.UUID) -> list[Product]:
        return list(self.db.scalars(select(Product).where(Product.shop_id == shop_id).order_by(Product.name)))

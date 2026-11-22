import uuid
from datetime import datetime, time

import pytest

from app.core.database import SessionLocal
from app.core.geo import haversine_km
from app.core.text import fold
from app.core.timeutil import TURKEY_TZ, is_open_at
from app.models import Product, Shop

API = "/api/v1/shops"
KIZILAY = {"lat": 39.9200, "lng": 32.8550}  # Kızılay Meydanı civarı


def names(res) -> list[str]:
    return [s["name"] for s in res.json()["data"]["items"]]


def pin_time(monkeypatch, hour: int, minute: int = 0):
    monkeypatch.setattr(
        "app.services.shop_service.turkey_now", lambda: datetime(2026, 6, 1, hour, minute, tzinfo=TURKEY_TZ)
    )


# ---- yardımcı fonksiyonlar (birim testler) --------------------------------------------------

def test_haversine_known_distances():
    assert haversine_km(39.92, 32.85, 39.92, 32.85) == 0
    assert haversine_km(39.9208, 32.8541, 39.8870, 32.6890) == pytest.approx(14.6, abs=0.3)  # Kızılay-Çayyolu
    assert haversine_km(41.0082, 28.9784, 39.9334, 32.8597) == pytest.approx(350, abs=10)  # İstanbul-Ankara


def test_fold_ignores_case_and_turkish_letters():
    assert fold("KIZILAY") == fold("Kızılay") == fold("kizilay")
    assert fold("ÇAYYOLU") == fold("çayyolu") == "cayyolu"
    assert fold("Hamamönü") == fold("HAMAMONU")


def test_opening_hours_logic():
    assert is_open_at("08:00", "22:00", time(12, 0)) is True
    assert is_open_at("08:00", "22:00", time(22, 0)) is False  # kapanış anı kapalı
    assert is_open_at("08:00", "22:00", time(7, 59)) is False
    assert is_open_at("10:00", "00:00", time(23, 59)) is True  # gece yarısı kapanış
    assert is_open_at("10:00", "00:00", time(0, 30)) is False
    assert is_open_at("18:00", "02:00", time(1, 0)) is True  # gece yarısını aşan
    assert is_open_at("18:00", "02:00", time(12, 0)) is False
    assert is_open_at("00:00", "00:00", time(15, 0)) is True  # 7/24


# ---- listeleme ------------------------------------------------------------------------------

def test_list_all_shops_is_public_and_alphabetical(client, shops):
    res = client.get(API)  # giriş yok
    data = res.json()["data"]
    assert res.status_code == 200 and data["total"] == 5
    assert names(res) == sorted(names(res), key=fold)
    first = data["items"][0]
    assert first["distance_km"] is None and isinstance(first["is_open"], bool)
    assert "owner_id" not in first


def test_nearby_sorted_by_distance(client, shops):
    res = client.get(API, params=KIZILAY)
    assert names(res) == ["Güvenpark Kahve", "Tunalı Roastery", "Hamamönü Kahvesi", "7. Cadde Kahve Evi", "Çayyolu Bean"]
    distances = [s["distance_km"] for s in res.json()["data"]["items"]]
    assert distances == sorted(distances)
    assert distances[0] < 0.2 and 14 < distances[-1] < 15.5


def test_radius_filters_by_distance(client, shops):
    assert names(client.get(API, params={**KIZILAY, "radius": 1})) == ["Güvenpark Kahve"]
    assert "Çayyolu Bean" not in names(client.get(API, params={**KIZILAY, "radius": 3}))
    assert len(names(client.get(API, params={**KIZILAY, "radius": 3}))) == 4
    # Çayyolu ~14.6 km: 14 km'de dışarıda, 15 km'de içeride (ön eleme kutusu sınırdaki dükkânı kaçırmamalı)
    assert len(names(client.get(API, params={**KIZILAY, "radius": 14}))) == 4
    assert len(names(client.get(API, params={**KIZILAY, "radius": 15}))) == 5


def test_location_validation(client, shops):
    only_lat = client.get(API, params={"lat": 39.9})
    assert only_lat.status_code == 400 and only_lat.json()["error"]["code"] == "LOCATION_INCOMPLETE"
    no_loc = client.get(API, params={"radius": 5})
    assert no_loc.status_code == 400 and no_loc.json()["error"]["code"] == "LOCATION_REQUIRED"
    assert client.get(API, params={"sort": "distance"}).status_code == 400
    assert client.get(API, params={"lat": 999, "lng": 32}).status_code == 422
    assert client.get(API, params={**KIZILAY, "radius": -1}).status_code == 422


@pytest.mark.parametrize(
    "query, expected",
    [
        ("kizilay", ["Güvenpark Kahve"]),  # adreste, Türkçe karaktersiz
        ("KIZILAY", ["Güvenpark Kahve"]),
        ("roastery", ["Tunalı Roastery"]),  # isimde
        ("HAMAMONU", ["Hamamönü Kahvesi"]),
        ("çayyolu", ["Çayyolu Bean"]),
        ("cankaya", ["7. Cadde Kahve Evi", "Çayyolu Bean", "Güvenpark Kahve", "Tunalı Roastery"]),
        ("yokboylebirsey", []),
    ],
)
def test_search_by_name_or_address(client, shops, query, expected):
    assert set(names(client.get(API, params={"q": query}))) == set(expected)


def test_search_combined_with_location_keeps_distance_order(client, shops):
    res = client.get(API, params={**KIZILAY, "q": "cankaya"})
    assert names(res) == ["Güvenpark Kahve", "Tunalı Roastery", "7. Cadde Kahve Evi", "Çayyolu Bean"]


def test_min_rating_and_rating_sort(client, shops):
    assert set(names(client.get(API, params={"min_rating": 4.7}))) == {"Hamamönü Kahvesi", "Tunalı Roastery"}
    res = client.get(API, params={"sort": "rating"})
    ratings = [s["rating"] for s in res.json()["data"]["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_open_closed_filter(client, shops, monkeypatch):
    pin_time(monkeypatch, 22, 45)  # Tunalı (22:30) ve Çayyolu (22:00) kapanmış
    open_now = client.get(API, params={"is_open": True})
    closed = client.get(API, params={"is_open": False})
    assert set(names(open_now)) == {"7. Cadde Kahve Evi", "Güvenpark Kahve", "Hamamönü Kahvesi"}
    assert set(names(closed)) == {"Çayyolu Bean", "Tunalı Roastery"}
    flags = {s["name"]: s["is_open"] for s in client.get(API).json()["data"]["items"]}
    assert flags["Tunalı Roastery"] is False and flags["Güvenpark Kahve"] is True

    pin_time(monkeypatch, 3)  # gece 3: hepsi kapalı
    assert client.get(API, params={"is_open": True}).json()["data"]["total"] == 0


def test_pagination(client, shops):
    res = client.get(API, params={"limit": 2, "offset": 1})
    data = res.json()["data"]
    assert data["total"] == 5 and len(data["items"]) == 2
    all_names = names(client.get(API))
    assert names(res) == all_names[1:3]


def test_inactive_shop_is_hidden(client, shops):
    with SessionLocal() as db:
        shop = db.query(Shop).filter_by(name="Çayyolu Bean").one()
        shop.is_active = False
        shop_id = str(shop.id)
        db.commit()
    assert "Çayyolu Bean" not in names(client.get(API))
    assert client.get(f"{API}/{shop_id}").status_code == 404
    assert client.get(f"{API}/{shop_id}/menu").status_code == 404


# ---- detay ve menü --------------------------------------------------------------------------

def _shop_id(client, name):
    return next(s["id"] for s in client.get(API).json()["data"]["items"] if s["name"] == name)


def test_shop_detail_includes_menu(client, shops):
    res = client.get(f"{API}/{_shop_id(client, 'Güvenpark Kahve')}")
    data = res.json()["data"]
    assert res.status_code == 200
    assert data["name"] == "Güvenpark Kahve" and data["distance_km"] is None
    assert len(data["menu"]) == 5
    assert {"Espresso", "Türk Kahvesi"} <= {p["name"] for p in data["menu"]}
    assert data["menu"][0]["base_price"] > 0 and data["menu"][0]["is_available"] is True


def test_shop_detail_with_location_has_distance(client, shops):
    shop_id = _shop_id(client, "Çayyolu Bean")
    data = client.get(f"{API}/{shop_id}", params=KIZILAY).json()["data"]
    assert 14 < data["distance_km"] < 15.5
    assert client.get(f"{API}/{shop_id}", params={"lat": 39.9}).status_code == 400


def test_menu_endpoint_marks_unavailable_products(client, shops):
    shop_id = _shop_id(client, "Hamamönü Kahvesi")
    with SessionLocal() as db:
        product = db.query(Product).filter_by(shop_id=uuid.UUID(shop_id), name="Salep").one()
        product.is_available = False
        db.commit()
    menu = client.get(f"{API}/{shop_id}/menu").json()["data"]
    assert len(menu) == 4
    assert {p["name"]: p["is_available"] for p in menu}["Salep"] is False


def test_unknown_or_malformed_shop_id(client, shops):
    missing = client.get(f"{API}/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "SHOP_NOT_FOUND"
    bad = client.get(f"{API}/abc")
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "VALIDATION_ERROR"


# ---- ürün kategorisi -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("Espresso", "espresso"), ("Americano", "espresso"), ("Cappuccino", "espresso"), ("Latte", "espresso"),
        ("Flat White", "espresso"), ("Mocha", "espresso"),
        ("Filtre Kahve", "filter"), ("V60", "filter"),
        ("Cold Brew", "cold"), ("Iced Latte", "cold"),  # soğuk olan, espresso bazlıdan önce gelir
        ("Türk Kahvesi", "other"), ("Menengiç Kahvesi", "other"), ("Dibek Kahvesi", "other"),
        ("Sıcak Çikolata", "other"), ("Salep", "other"),
    ],
)
def test_product_category_from_name(name, expected):
    from app.core.categories import category_for

    assert category_for(name) == expected


def test_menu_returns_category(client, shops):
    shop_id = _shop_id(client, "Tunalı Roastery")
    menu = client.get(f"{API}/{shop_id}/menu").json()["data"]
    categories = {p["name"]: p["category"] for p in menu}
    assert categories == {
        "Espresso": "espresso", "Flat White": "espresso", "Cappuccino": "espresso", "Mocha": "espresso",
        "Filtre Kahve": "filter", "Cold Brew": "cold",
    }
    detail = client.get(f"{API}/{shop_id}").json()["data"]
    assert all("category" in p for p in detail["menu"])

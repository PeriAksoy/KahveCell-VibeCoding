import os
import tempfile

# Testler gerçek veritabanına dokunmasın: uygulama içe aktarılmadan ÖNCE geçici bir dosya gösteriyoruz.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402


@pytest.fixture()
def client():
    from decimal import Decimal

    from app.models import Plan

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # Paketler sabit referans veridir; seed.py'deki tanımı aynen kullanıyoruz.
    from seed import PLANS

    with SessionLocal() as db:
        for code, name, price, credits, guests, priority in PLANS:
            db.add(Plan(code=code, name=name, monthly_price=Decimal(price), monthly_credits=credits,
                        guest_passes=guests, has_priority=priority))
        db.commit()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def shops(client):
    """seed.py'deki 5 Ankara dükkânını (gerçek koordinatlar ve menülerle) test veritabanına ekler."""
    from seed import SHOPS, add_shop

    with SessionLocal() as db:
        for i, spec in enumerate(SHOPS, start=1):
            owner = User(phone_number=f"+90555888000{i}", role=UserRole.SHOP_OWNER)
            db.add(owner)
            db.flush()
            add_shop(db, owner, spec)
        db.commit()


@pytest.fixture()
def login(client):
    """login("5551234567") -> verify-otp cevabının 'data' kısmı (tokenlar + kullanıcı)."""

    def _login(phone: str = "5551234567") -> dict:
        client.post("/api/v1/auth/register", json={"phone_number": phone})
        res = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "code": "1234"})
        assert res.status_code == 200, res.text
        return res.json()["data"]

    return _login


@pytest.fixture()
def make_user_with_role():
    def _make(phone: str, role: UserRole) -> None:
        with SessionLocal() as db:
            db.add(User(phone_number=phone, full_name="Test", role=role))
            db.commit()

    return _make


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

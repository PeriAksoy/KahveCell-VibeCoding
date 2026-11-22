import json
import uuid

import pytest

from app.core.database import SessionLocal
from app.models import Order, Subscription
from app.models.enums import UserRole
from tests.conftest import auth_header

API = "/api/v1"
CARD = {"card_holder": "Test", "card_number": "4242424242424242", "expiry_month": 12, "expiry_year": 2035, "cvc": "123"}


# ---- hazırlık ---------------------------------------------------------------------------------

@pytest.fixture()
def make_customer(client, login):
    def _make(phone="5551110001", plan="STARTER"):
        headers = auth_header(login(phone)["access_token"])
        if plan:
            res = client.post(f"{API}/subscriptions", headers=headers, json={"plan_code": plan, "card": CARD})
            assert res.status_code == 201, res.text
        return headers

    return _make


@pytest.fixture()
def owner(client, login, shops):  # Güvenpark Kahve'nin sahibi
    return auth_header(login("5558880001")["access_token"])


@pytest.fixture()
def other_owner(client, login, shops):  # Tunalı Roastery'nin sahibi
    return auth_header(login("5558880002")["access_token"])


@pytest.fixture()
def menu(client, shops):
    """Güvenpark Kahve'nin id'si ve ürünleri."""
    items = client.get(f"{API}/shops").json()["data"]["items"]
    shop = next(s for s in items if s["name"] == "Güvenpark Kahve")
    products = client.get(f"{API}/shops/{shop['id']}/menu").json()["data"]
    return {"shop_id": shop["id"], "latte": next(p["id"] for p in products if p["name"] == "Cappuccino")}


def place(client, headers, menu, **options):
    body = {"shop_id": menu["shop_id"], "product_id": menu["latte"], **options}
    return client.post(f"{API}/orders", headers=headers, json=body)


def create(client, headers, menu, **options) -> dict:
    res = place(client, headers, menu, **options)
    assert res.status_code == 201, res.text
    return res.json()["data"]["order"]


def set_status_call(client, headers, order_id, status, qr=None):
    return client.patch(f"{API}/orders/{order_id}/status", headers=headers, json={"status": status, "qr": qr})


def credits() -> int | None:
    with SessionLocal() as db:
        return db.query(Subscription).first().remaining_credits


def set_credits(value):
    with SessionLocal() as db:
        db.query(Subscription).first().remaining_credits = value
        db.commit()


def order_count() -> int:
    with SessionLocal() as db:
        return db.query(Order).count()


# ---- sipariş verme ve hak düşümü -----------------------------------------------------------------

def test_create_order_deducts_one_credit_and_returns_qr(client, make_customer, menu):
    headers = make_customer()
    res = place(client, headers, menu, size="L", sugar_level=2, milk_type="oat", extra_shots=1)
    assert res.status_code == 201
    data = res.json()["data"]
    order = data["order"]
    assert data["remaining_credits"] == 9 and credits() == 9
    assert order["status"] == "PENDING" and order["status_label"] == "Onay bekliyor"
    assert (order["size"], order["sugar_level"], order["milk_type"], order["extra_shots"]) == ("L", 2, "oat", 1)
    assert order["product"]["name"] == "Cappuccino" and order["shop"]["name"] == "Güvenpark Kahve"

    qr = order["qr_payload"]
    assert list(qr) == ["order_id", "user_id", "shop_id", "created_at", "signature"]  # case 13.2 alanları
    assert qr["order_id"] == order["id"] and qr["shop_id"] == menu["shop_id"]
    assert qr["created_at"].endswith("Z") and len(qr["signature"]) == 64
    assert order["qr_image"].startswith("data:image/png;base64,")


def test_defaults_when_no_options_given(client, make_customer, menu):
    order = create(client, make_customer(), menu)
    assert (order["size"], order["sugar_level"], order["milk_type"], order["extra_shots"]) == ("M", 0, None, 0)


def test_unlimited_plan_never_deducts(client, make_customer, menu):
    headers = make_customer(plan="UNLIMITED")
    for _ in range(3):
        res = place(client, headers, menu)
        assert res.status_code == 201 and res.json()["data"]["remaining_credits"] is None
    assert credits() is None and order_count() == 3


def test_no_subscription_blocks_order(client, make_customer, menu):
    headers = make_customer(plan=None)
    res = place(client, headers, menu)
    assert res.status_code == 402
    assert res.json()["error"]["code"] == "SUBSCRIPTION_REQUIRED" and "aboneliğiniz" in res.json()["error"]["message"]
    assert order_count() == 0


def test_cancelled_subscription_blocks_order(client, make_customer, menu):
    headers = make_customer()
    client.delete(f"{API}/subscriptions/me", headers=headers)
    assert place(client, headers, menu).json()["error"]["code"] == "SUBSCRIPTION_REQUIRED"


def test_exhausted_credits_block_order_and_keep_zero(client, make_customer, menu):
    headers = make_customer()
    set_credits(0)
    res = place(client, headers, menu)
    assert res.status_code == 402
    err = res.json()["error"]
    assert err["code"] == "NO_CREDITS_LEFT" and "hakkınız bitti" in err["message"] and "yenilenecek" in err["message"]
    assert credits() == 0 and order_count() == 0


def test_last_credit_is_usable_exactly_once(client, make_customer, menu):
    headers = make_customer()
    set_credits(1)
    assert place(client, headers, menu).json()["data"]["remaining_credits"] == 0
    assert place(client, headers, menu).json()["error"]["code"] == "NO_CREDITS_LEFT"
    assert order_count() == 1


def test_order_validation(client, make_customer, menu):
    headers = make_customer()
    assert place(client, headers, menu, sugar_level=9).status_code == 422
    assert place(client, headers, menu, extra_shots=7).status_code == 422
    assert place(client, headers, menu, size="XL").status_code == 422
    assert place(client, headers, menu, milk_type="beer").status_code == 422
    unknown_shop = client.post(f"{API}/orders", headers=headers, json={"shop_id": str(uuid.uuid4()), "product_id": menu["latte"]})
    assert unknown_shop.status_code == 404 and unknown_shop.json()["error"]["code"] == "SHOP_NOT_FOUND"
    assert credits() == 10 and order_count() == 0  # hatalı denemeler hak harcamaz


def test_product_must_belong_to_chosen_shop(client, make_customer, menu):
    headers = make_customer()
    other = next(s for s in client.get(f"{API}/shops").json()["data"]["items"] if s["name"] == "Tunalı Roastery")
    res = client.post(f"{API}/orders", headers=headers, json={"shop_id": other["id"], "product_id": menu["latte"]})
    assert res.status_code == 404 and res.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert credits() == 10


def test_unavailable_product_is_rejected(client, make_customer, menu):
    from app.models import Product

    with SessionLocal() as db:
        db.get(Product, uuid.UUID(menu["latte"])).is_available = False
        db.commit()
    res = place(client, make_customer(), menu)
    assert res.status_code == 409 and res.json()["error"]["code"] == "PRODUCT_UNAVAILABLE"
    assert credits() == 10


def test_only_customers_can_order(client, owner, login, menu):
    assert place(client, owner, menu).status_code == 403
    assert client.post(f"{API}/orders", json={}).status_code == 401


# ---- takip: müşteri ve dükkân ------------------------------------------------------------------

def test_customer_and_shop_can_both_follow_the_order(client, make_customer, owner, other_owner, menu):
    me = make_customer("5551110001")
    order = create(client, me, menu)

    mine = client.get(f"{API}/orders/{order['id']}", headers=me).json()["data"]
    assert mine["qr_payload"] == order["qr_payload"]  # QR sahibine her seferinde aynı gelir
    assert [o["id"] for o in client.get(f"{API}/orders/history", headers=me).json()["data"]] == [order["id"]]

    theirs = client.get(f"{API}/orders/{order['id']}", headers=owner).json()["data"]
    assert theirs["qr_payload"] is None and theirs["qr_image"] is None  # dükkân QR'ı görmez
    queue = client.get(f"{API}/orders/shop", headers=owner).json()["data"]
    assert [o["id"] for o in queue] == [order["id"]]

    # başka dükkân sahibi ve başka müşteri siparişi göremez
    assert client.get(f"{API}/orders/{order['id']}", headers=other_owner).status_code == 404
    assert client.get(f"{API}/orders/shop", headers=other_owner).json()["data"] == []
    stranger = make_customer("5551110002")
    assert client.get(f"{API}/orders/{order['id']}", headers=stranger).status_code == 404
    assert client.get(f"{API}/orders/history", headers=stranger).json()["data"] == []


def test_role_separation_on_listing_endpoints(client, make_customer, owner, menu):
    me = make_customer()
    assert client.get(f"{API}/orders/shop", headers=me).status_code == 403
    assert client.get(f"{API}/orders/history", headers=owner).status_code == 403


def test_qr_png_endpoint(client, make_customer, menu):
    me = make_customer()
    order = create(client, me, menu)
    res = client.get(f"{API}/orders/{order['id']}/qr", headers=me)
    assert res.status_code == 200 and res.headers["content-type"] == "image/png"
    assert res.content.startswith(b"\x89PNG")
    assert client.get(f"{API}/orders/{order['id']}/qr", headers=make_customer("5551110002")).status_code == 404


def test_history_status_filter_and_order(client, make_customer, owner, menu):
    me = make_customer(plan="UNLIMITED")
    first, second = create(client, me, menu), create(client, me, menu)
    set_status_call(client, owner, first["id"], "ACCEPTED")
    history = client.get(f"{API}/orders/history", headers=me).json()["data"]
    assert [o["id"] for o in history] == [second["id"], first["id"]]  # en yeni önce
    accepted = client.get(f"{API}/orders/history", params={"status": "ACCEPTED"}, headers=me).json()["data"]
    assert [o["id"] for o in accepted] == [first["id"]]


def test_priority_customers_come_first_in_shop_queue(client, make_customer, owner, menu):
    regular = create(client, make_customer("5551110001", "STARTER"), menu)
    vip = create(client, make_customer("5551110002", "UNLIMITED"), menu)
    queue = client.get(f"{API}/orders/shop", headers=owner).json()["data"]
    assert [o["id"] for o in queue] == [vip["id"], regular["id"]]
    assert queue[0]["is_priority"] is True and queue[1]["is_priority"] is False


# ---- durum akışı ------------------------------------------------------------------------------------

def test_full_status_flow_to_delivery_with_qr(client, make_customer, owner, menu):
    me = make_customer()
    order = create(client, me, menu)
    oid, qr = order["id"], order["qr_payload"]

    for status, label in [("ACCEPTED", "Kabul edildi"), ("PREPARING", "Hazırlanıyor"), ("READY", "Hazır")]:
        res = set_status_call(client, owner, oid, status)
        assert res.status_code == 200 and res.json()["data"]["status_label"] == label
        # müşteri aynı anda güncel durumu görür
        assert client.get(f"{API}/orders/{oid}", headers=me).json()["data"]["status"] == status

    done = set_status_call(client, owner, oid, "COMPLETED", qr)
    assert done.status_code == 200 and done.json()["data"]["status_label"] == "Teslim edildi"
    # teslimden sonra kuyruktan çıkar, geçmiş filtresinde görünür
    assert client.get(f"{API}/orders/shop", headers=owner).json()["data"] == []
    finished = client.get(f"{API}/orders/shop", params={"status": "COMPLETED"}, headers=owner).json()["data"]
    assert [o["id"] for o in finished] == [oid]


def test_status_order_cannot_be_skipped_or_reversed(client, make_customer, owner, menu):
    order = create(client, make_customer(), menu)
    res = set_status_call(client, owner, order["id"], "READY")
    assert res.status_code == 409 and res.json()["error"]["code"] == "INVALID_TRANSITION"
    set_status_call(client, owner, order["id"], "ACCEPTED")
    assert set_status_call(client, owner, order["id"], "PENDING").status_code == 409
    assert set_status_call(client, owner, order["id"], "COMPLETED").status_code == 409  # henüz hazır değil


def test_delivery_requires_the_customers_qr(client, make_customer, owner, menu):
    order = create(client, make_customer(), menu)
    for status in ["ACCEPTED", "PREPARING", "READY"]:
        set_status_call(client, owner, order["id"], status)
    res = set_status_call(client, owner, order["id"], "COMPLETED")  # QR yok
    assert res.status_code == 400 and res.json()["error"]["code"] == "QR_REQUIRED"
    assert client.get(f"{API}/orders/{order['id']}", headers=owner).json()["data"]["status"] == "READY"


def test_qr_of_another_order_cannot_deliver(client, make_customer, owner, menu):
    me = make_customer(plan="UNLIMITED")
    a, b = create(client, me, menu), create(client, me, menu)
    for status in ["ACCEPTED", "PREPARING", "READY"]:
        set_status_call(client, owner, a["id"], status)
    res = set_status_call(client, owner, a["id"], "COMPLETED", b["qr_payload"])
    assert res.status_code == 400 and res.json()["error"]["code"] == "QR_MISMATCH"


def test_delivered_order_cannot_be_delivered_again(client, make_customer, owner, menu):
    order = create(client, make_customer(), menu)
    for status in ["ACCEPTED", "PREPARING", "READY"]:
        set_status_call(client, owner, order["id"], status)
    set_status_call(client, owner, order["id"], "COMPLETED", order["qr_payload"])
    again = set_status_call(client, owner, order["id"], "COMPLETED", order["qr_payload"])
    assert again.status_code == 409  # aynı QR ikinci kez kullanılamaz


def test_only_the_shops_owner_can_update_status(client, make_customer, owner, other_owner, menu):
    me = make_customer()
    order = create(client, me, menu)
    assert set_status_call(client, other_owner, order["id"], "ACCEPTED").status_code == 404
    assert set_status_call(client, me, order["id"], "ACCEPTED").status_code == 403
    assert set_status_call(client, owner, order["id"], "ACCEPTED").status_code == 200


# ---- QR sahteciliği -------------------------------------------------------------------------------

def verify(client, headers, qr):
    return client.post(f"{API}/orders/verify-qr", headers=headers, json={"qr": qr})


def test_verify_real_qr_says_authentic_and_changes_nothing(client, make_customer, owner, menu):
    order = create(client, make_customer(), menu)
    res = verify(client, owner, order["qr_payload"])
    data = res.json()["data"]
    assert res.status_code == 200 and data["authentic"] is True
    assert data["can_deliver"] is False and "henüz hazır değil" in data["message"]  # gerçek ama hazır değil

    for status in ["ACCEPTED", "PREPARING", "READY"]:
        set_status_call(client, owner, order["id"], status)
    ready = verify(client, owner, order["qr_payload"]).json()["data"]
    assert ready["can_deliver"] is True and ready["order"]["status"] == "READY"  # doğrulama durumu değiştirmedi

    set_status_call(client, owner, order["id"], "COMPLETED", order["qr_payload"])
    used = verify(client, owner, order["qr_payload"]).json()["data"]
    assert used["authentic"] is True and used["can_deliver"] is False and "zaten teslim" in used["message"]


@pytest.mark.parametrize(
    "tamper",
    [
        lambda qr: {**qr, "signature": "0" * 64},  # imza uydurma
        lambda qr: {**qr, "signature": qr["signature"][:-1] + ("0" if qr["signature"][-1] != "0" else "1")},  # 1 karakter oynama
        lambda qr: {**qr, "created_at": "2020-01-01T00:00:00.000Z"},  # tarih değişti
        lambda qr: {**qr, "user_id": str(uuid.uuid4())},  # başka kullanıcı
        lambda qr: {**qr, "shop_id": str(uuid.uuid4())},  # başka dükkân
        lambda qr: {**qr, "order_id": str(uuid.uuid4())},  # olmayan sipariş
    ],
)
def test_forged_or_tampered_qr_is_rejected(client, make_customer, owner, menu, tamper):
    order = create(client, make_customer(), menu)
    res = verify(client, owner, tamper(order["qr_payload"]))
    assert res.status_code == 400 and res.json()["error"]["code"] == "INVALID_QR"


def test_forged_qr_cannot_deliver_an_order(client, make_customer, owner, menu):
    order = create(client, make_customer(), menu)
    for status in ["ACCEPTED", "PREPARING", "READY"]:
        set_status_call(client, owner, order["id"], status)
    forged = {**order["qr_payload"], "signature": "ab" * 32}
    res = set_status_call(client, owner, order["id"], "COMPLETED", forged)
    assert res.status_code == 400 and res.json()["error"]["code"] == "INVALID_QR"
    assert client.get(f"{API}/orders/{order['id']}", headers=owner).json()["data"]["status"] == "READY"


def test_qr_signed_with_another_secret_is_rejected(client, make_customer, owner, menu, monkeypatch):
    order = create(client, make_customer(), menu)
    # Saldırganın kendi anahtarıyla imzalaması: sunucu farklı anahtar kullandığı için imza eşleşmez.
    monkeypatch.setattr("app.services.qr_service._key", lambda: b"baska-bir-anahtar-0123456789abcdef")
    res = verify(client, owner, order["qr_payload"])
    assert res.status_code == 400 and res.json()["error"]["code"] == "INVALID_QR"


def test_qr_of_another_shop_is_refused(client, make_customer, other_owner, menu):
    order = create(client, make_customer(), menu)  # Güvenpark siparişi
    res = verify(client, other_owner, order["qr_payload"])  # Tunalı sahibi okutuyor
    assert res.status_code == 403 and res.json()["error"]["code"] == "WRONG_SHOP"


def test_qr_content_matches_case_format(client, make_customer, menu):
    from app.schemas.order import QrPayload
    from app.services.qr_service import to_content

    qr = create(client, make_customer(), menu)["qr_payload"]
    content = json.loads(to_content(QrPayload(**qr)))
    assert list(content) == ["order_id", "user_id", "shop_id", "created_at", "signature"]
    assert content == qr


# ---- iptal ve tekrar sipariş -----------------------------------------------------------------

def test_customer_cancel_refunds_credit_only_while_pending(client, make_customer, owner, menu):
    me = make_customer()
    order = create(client, me, menu)
    assert credits() == 9
    res = client.post(f"{API}/orders/{order['id']}/cancel", headers=me)
    assert res.status_code == 200 and res.json()["data"]["status"] == "CANCELLED"
    assert credits() == 10  # hak iade edildi

    second = create(client, me, menu)
    set_status_call(client, owner, second["id"], "ACCEPTED")
    late = client.post(f"{API}/orders/{second['id']}/cancel", headers=me)
    assert late.status_code == 409 and late.json()["error"]["code"] == "CANNOT_CANCEL"
    assert credits() == 9


def test_shop_cancel_refunds_credit_and_cancelled_qr_is_dead(client, make_customer, owner, menu):
    me = make_customer()
    order = create(client, me, menu)
    set_status_call(client, owner, order["id"], "ACCEPTED")
    assert set_status_call(client, owner, order["id"], "CANCELLED").status_code == 200
    assert credits() == 10
    res = verify(client, owner, order["qr_payload"]).json()["data"]
    assert res["authentic"] is True and res["can_deliver"] is False and "iptal" in res["message"]


def test_refund_never_exceeds_monthly_allowance(client, make_customer, menu):
    me = make_customer()
    order = create(client, me, menu)
    set_credits(10)  # (örn. araya yenileme girdi) hak zaten tavanda
    client.post(f"{API}/orders/{order['id']}/cancel", headers=me)
    assert credits() == 10


def test_unlimited_cancel_keeps_unlimited(client, make_customer, menu):
    me = make_customer(plan="UNLIMITED")
    order = create(client, me, menu)
    client.post(f"{API}/orders/{order['id']}/cancel", headers=me)
    assert credits() is None


def test_reorder_repeats_options_and_deducts_again(client, make_customer, menu):
    me = make_customer()
    first = create(client, me, menu, size="L", sugar_level=3, milk_type="almond", extra_shots=2)
    res = client.post(f"{API}/orders/{first['id']}/reorder", headers=me)
    assert res.status_code == 201
    data = res.json()["data"]
    again = data["order"]
    assert again["id"] != first["id"] and data["remaining_credits"] == 8
    assert (again["size"], again["sugar_level"], again["milk_type"], again["extra_shots"]) == ("L", 3, "almond", 2)
    assert again["qr_payload"]["signature"] != first["qr_payload"]["signature"]
    assert client.post(f"{API}/orders/{first['id']}/reorder", headers=make_customer("5551110002")).status_code == 404

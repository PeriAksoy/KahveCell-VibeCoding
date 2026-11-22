from datetime import timedelta

import pytest

from app.core.database import SessionLocal
from app.models import Subscription
from app.models.enums import UserRole
from app.models.user import utcnow
from tests.conftest import auth_header

API = "/api/v1"

GOOD_CARD = {"card_holder": "Test Kullanıcı", "card_number": "4242 4242 4242 4242",
             "expiry_month": 12, "expiry_year": 2035, "cvc": "123"}
DECLINED_CARD = {**GOOD_CARD, "card_number": "4000-0000-0000-0002"}
UNKNOWN_CARD = {**GOOD_CARD, "card_number": "5555555555554444"}


@pytest.fixture()
def me(login):
    data = login()
    return auth_header(data["access_token"])


def subscribe(client, headers, plan="STARTER", card=GOOD_CARD):
    return client.post(f"{API}/subscriptions", headers=headers, json={"plan_code": plan, "card": card})


def change(client, headers, plan, card=None):
    return client.patch(f"{API}/subscriptions/me", headers=headers, json={"plan_code": plan, "card": card})


def set_credits(value):
    with SessionLocal() as db:
        sub = db.query(Subscription).first()
        sub.remaining_credits = value
        db.commit()


def test_plans_are_public_and_match_case_document(client):
    res = client.get(f"{API}/subscriptions/plans")
    plans = res.json()["data"]
    assert [p["code"] for p in plans] == ["STARTER", "PREMIUM", "UNLIMITED"]
    assert [p["monthly_price"] for p in plans] == [89.99, 149.99, 249.99]
    assert [p["monthly_credits"] for p in plans] == [10, 20, None]
    assert plans[2]["is_unlimited"] is True


def test_subscribe_success_grants_credits_and_records_payment(client, me):
    res = subscribe(client, me)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["subscription"]["status"] == "ACTIVE"
    assert data["subscription"]["remaining_credits"] == 10
    assert data["payment"]["status"] == "SUCCESS"
    assert data["payment"]["amount"] == 89.99
    assert data["payment"]["card_last4"] == "4242"
    assert "card_number" not in str(data)

    mine = client.get(f"{API}/subscriptions/me", headers=me).json()["data"]
    assert mine["plan"]["code"] == "STARTER" and mine["remaining_credits"] == 10


def test_unlimited_plan_has_no_credit_limit(client, me):
    data = subscribe(client, me, "UNLIMITED").json()["data"]
    assert data["subscription"]["remaining_credits"] is None
    assert data["subscription"]["is_unlimited"] is True


def test_declined_card_creates_no_subscription_but_is_logged(client, me):
    res = subscribe(client, me, card=DECLINED_CARD)
    assert res.status_code == 402
    assert res.json()["error"]["code"] == "PAYMENT_FAILED"
    assert client.get(f"{API}/subscriptions/me", headers=me).status_code == 404

    history = client.get(f"{API}/payments/me", headers=me).json()["data"]
    assert len(history) == 1 and history[0]["status"] == "FAILED" and history[0]["card_last4"] == "0002"


def test_unknown_card_is_rejected_in_simulation(client, me):
    res = subscribe(client, me, card=UNKNOWN_CARD)
    assert res.status_code == 402
    assert client.get(f"{API}/subscriptions/me", headers=me).status_code == 404


def test_invalid_card_form_is_rejected(client, me):
    assert subscribe(client, me, card={**GOOD_CARD, "card_number": "1234"}).status_code == 422
    assert subscribe(client, me, card={**GOOD_CARD, "expiry_year": 2020}).status_code == 422
    assert subscribe(client, me, card={**GOOD_CARD, "cvc": "12"}).status_code == 422


def test_cannot_subscribe_twice(client, me):
    subscribe(client, me)
    res = subscribe(client, me, "PREMIUM")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_SUBSCRIBED"


def test_no_subscription_gives_404(client, me):
    res = client.get(f"{API}/subscriptions/me", headers=me)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NO_ACTIVE_SUBSCRIPTION"


def test_upgrade_charges_difference_and_adds_credits(client, me):
    subscribe(client, me, "STARTER")
    set_credits(7)  # 3 kahve içilmiş gibi
    res = change(client, me, "PREMIUM", GOOD_CARD)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["subscription"]["plan"]["code"] == "PREMIUM"
    assert data["subscription"]["remaining_credits"] == 17  # 7 + (20 - 10)
    assert data["payment"]["amount"] == 60.0  # 149.99 - 89.99


def test_upgrade_to_unlimited_removes_limit(client, me):
    subscribe(client, me, "STARTER")
    data = change(client, me, "UNLIMITED", GOOD_CARD).json()["data"]
    assert data["subscription"]["remaining_credits"] is None
    assert data["payment"]["amount"] == 160.0


def test_upgrade_requires_card_and_failed_payment_changes_nothing(client, me):
    subscribe(client, me, "STARTER")
    assert change(client, me, "PREMIUM").json()["error"]["code"] == "CARD_REQUIRED"
    assert change(client, me, "PREMIUM", DECLINED_CARD).status_code == 402
    mine = client.get(f"{API}/subscriptions/me", headers=me).json()["data"]
    assert mine["plan"]["code"] == "STARTER" and mine["remaining_credits"] == 10


def test_downgrade_is_free_and_caps_credits(client, me):
    subscribe(client, me, "PREMIUM")
    data = change(client, me, "STARTER").json()["data"]
    assert data["payment"] is None
    assert data["subscription"]["plan"]["code"] == "STARTER"
    assert data["subscription"]["remaining_credits"] == 10  # 20 -> yeni paketin tavanı


def test_downgrade_keeps_lower_remaining_credits(client, me):
    subscribe(client, me, "PREMIUM")
    set_credits(4)
    assert change(client, me, "STARTER").json()["data"]["subscription"]["remaining_credits"] == 4


def test_downgrade_from_unlimited_gets_plan_credits(client, me):
    subscribe(client, me, "UNLIMITED")
    assert change(client, me, "PREMIUM").json()["data"]["subscription"]["remaining_credits"] == 20


def test_same_plan_is_rejected(client, me):
    subscribe(client, me, "STARTER")
    res = change(client, me, "STARTER", GOOD_CARD)
    assert res.status_code == 409 and res.json()["error"]["code"] == "SAME_PLAN"


def test_cancel_then_resubscribe(client, me):
    subscribe(client, me)
    res = client.delete(f"{API}/subscriptions/me", headers=me)
    assert res.json()["data"]["status"] == "CANCELLED"
    assert client.get(f"{API}/subscriptions/me", headers=me).status_code == 404
    assert client.delete(f"{API}/subscriptions/me", headers=me).status_code == 404
    assert subscribe(client, me, "PREMIUM").status_code == 201  # iptal sonrası yeniden abone olunabilir


def test_monthly_renewal_resets_credits_and_logs_payment(client, me):
    subscribe(client, me, "STARTER")
    set_credits(2)
    with SessionLocal() as db:  # dönemi bitmiş gibi göster
        sub = db.query(Subscription).first()
        sub.expires_at = utcnow() - timedelta(days=1)
        db.commit()

    mine = client.get(f"{API}/subscriptions/me", headers=me).json()["data"]
    assert mine["remaining_credits"] == 10
    history = client.get(f"{API}/payments/me", headers=me).json()["data"]
    assert len(history) == 2
    assert history[0]["transaction_id"].startswith("RNW-") and history[0]["status"] == "SUCCESS"
    # yenilemeden sonra tekrar bakınca yeni ödeme alınmamalı
    client.get(f"{API}/subscriptions/me", headers=me)
    assert len(client.get(f"{API}/payments/me", headers=me).json()["data"]) == 2


def test_only_customers_can_subscribe(client, login, make_user_with_role):
    make_user_with_role("+905559990001", UserRole.SHOP_OWNER)
    owner = auth_header(login("5559990001")["access_token"])
    assert subscribe(client, owner).status_code == 403


def test_requires_login(client):
    assert client.post(f"{API}/subscriptions", json={"plan_code": "STARTER", "card": GOOD_CARD}).status_code == 401
    assert client.get(f"{API}/subscriptions/me").status_code == 401
    assert client.get(f"{API}/payments/me").status_code == 401

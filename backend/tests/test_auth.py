from tests.conftest import auth_header

API = "/api/v1"


def test_register_creates_customer_and_normalizes_phone(client):
    res = client.post(f"{API}/auth/register", json={"phone_number": "0555 123 45 67"})
    body = res.json()
    assert res.status_code == 200
    assert body["success"] is True and body["error"] is None
    assert body["data"]["phone_number"] == "+905551234567"
    assert body["data"]["is_new_user"] is True


def test_register_twice_is_login_not_duplicate(client):
    client.post(f"{API}/auth/register", json={"phone_number": "5551234567"})
    res = client.post(f"{API}/auth/register", json={"phone_number": "+90 555 123 45 67"})
    assert res.json()["data"]["is_new_user"] is False


def test_login_sends_otp_only_to_registered_numbers(client):
    unknown = client.post(f"{API}/auth/login", json={"phone_number": "5559998877"})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "USER_NOT_FOUND"

    client.post(f"{API}/auth/register", json={"phone_number": "5551234567"})
    known = client.post(f"{API}/auth/login", json={"phone_number": "0555 123 45 67"})
    assert known.status_code == 200 and known.json()["data"]["is_new_user"] is False

    # başarısız giriş denemesi hesap OLUŞTURMAMALI: aynı numara hâlâ "yeni" sayılır
    again = client.post(f"{API}/auth/register", json={"phone_number": "5559998877"})
    assert again.json()["data"]["is_new_user"] is True


def test_register_rejects_invalid_phone(client):
    res = client.post(f"{API}/auth/register", json={"phone_number": "12345"})
    body = res.json()
    assert res.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_verify_wrong_code_fails(client):
    client.post(f"{API}/auth/register", json={"phone_number": "5551234567"})
    res = client.post(f"{API}/auth/verify-otp", json={"phone_number": "5551234567", "code": "9999"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_OTP"


def test_verify_unregistered_phone_gives_same_error(client):
    res = client.post(f"{API}/auth/verify-otp", json={"phone_number": "5559999999", "code": "1234"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_OTP"


def test_login_flow_and_profile_completion(client, login):
    data = login()
    assert data["user"]["role"] == "CUSTOMER"
    assert data["user"]["profile_complete"] is False

    headers = auth_header(data["access_token"])
    assert client.get(f"{API}/users/me", headers=headers).json()["data"]["phone_number"] == "+905551234567"

    res = client.patch(
        f"{API}/users/me",
        headers=headers,
        json={"full_name": "Ayşe Yılmaz", "email": "ayse@example.com", "preferences": {"coffees": ["Latte"], "allergens": ["fındık"]}},
    )
    me = res.json()["data"]
    assert me["profile_complete"] is True
    assert me["preferences"]["allergens"] == ["fındık"]


def test_email_must_be_unique(client, login):
    a = login("5551111111")
    b = login("5552222222")
    client.patch(f"{API}/users/me", headers=auth_header(a["access_token"]), json={"email": "x@example.com"})
    res = client.patch(f"{API}/users/me", headers=auth_header(b["access_token"]), json={"email": "x@example.com"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_TAKEN"


def test_protected_endpoint_requires_valid_token(client):
    assert client.get(f"{API}/users/me").status_code == 401
    res = client.get(f"{API}/users/me", headers=auth_header("sahte.token.degeri"))
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"


def test_refresh_token_cannot_be_used_as_access_token(client, login):
    data = login()
    res = client.get(f"{API}/users/me", headers=auth_header(data["refresh_token"]))
    assert res.status_code == 401


def test_refresh_rotates_and_old_token_is_dead(client, login):
    data = login()
    first = client.post(f"{API}/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert first.status_code == 200
    new_pair = first.json()["data"]
    assert new_pair["refresh_token"] != data["refresh_token"]
    assert client.get(f"{API}/users/me", headers=auth_header(new_pair["access_token"])).status_code == 200

    # Eski refresh token tekrar kullanılırsa reddedilir ve o kullanıcının tüm oturumları kapanır.
    reuse = client.post(f"{API}/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "TOKEN_REVOKED"
    after = client.post(f"{API}/auth/refresh", json={"refresh_token": new_pair["refresh_token"]})
    assert after.status_code == 401


def test_access_token_cannot_be_used_to_refresh(client, login):
    data = login()
    res = client.post(f"{API}/auth/refresh", json={"refresh_token": data["access_token"]})
    assert res.status_code == 401


def test_logout_revokes_refresh_token(client, login):
    data = login()
    assert client.post(f"{API}/auth/logout", json={"refresh_token": data["refresh_token"]}).status_code == 200
    res = client.post(f"{API}/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert res.status_code == 401


def test_roles_customer_forbidden_admin_allowed(client, login, make_user_with_role):
    from app.models.enums import UserRole

    customer = login("5551111111")
    res = client.get(f"{API}/users", headers=auth_header(customer["access_token"]))
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    make_user_with_role("+905550000000", UserRole.ADMIN)
    admin = login("5550000000")
    assert admin["user"]["role"] == "ADMIN"
    res = client.get(f"{API}/users", headers=auth_header(admin["access_token"]))
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2


def test_cannot_self_assign_role(client, login):
    data = login()
    client.patch(f"{API}/users/me", headers=auth_header(data["access_token"]), json={"role": "ADMIN"})
    me = client.get(f"{API}/users/me", headers=auth_header(data["access_token"])).json()["data"]
    assert me["role"] == "CUSTOMER"

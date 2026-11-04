from datetime import UTC, datetime, timedelta

import jwt

from app import rate_limit
from app.config import settings

USER = {"username": "karim", "email": "Karim@Example.com", "password": "correct-horse"}


def login(client, username=USER["username"], password=USER["password"]):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_signup_login_me(client):
    created = client.post("/auth/signup", json=USER)
    assert created.status_code == 201
    assert "password" not in created.text and "password_hash" not in created.text
    assert created.json()["email"] == "karim@example.com"

    token = login(client).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "karim"


def test_login_with_email_any_case(client):
    client.post("/auth/signup", json=USER)
    assert login(client, username="KARIM@example.com").status_code == 200


def test_duplicates_rejected(client):
    client.post("/auth/signup", json=USER)
    assert client.post("/auth/signup", json=USER).status_code == 409
    assert client.post("/auth/signup", json={**USER, "username": "other"}).status_code == 409
    assert client.post("/auth/signup", json={**USER, "email": "other@example.com"}).status_code == 409


def test_bad_credentials(client):
    client.post("/auth/signup", json=USER)
    assert login(client, password="wrong-password").status_code == 401
    assert login(client, username="nobody").status_code == 401
    assert login(client, password="x" * 100).status_code == 401


def test_password_length_limits(client):
    assert client.post("/auth/signup", json={**USER, "password": "short"}).status_code == 422
    assert client.post("/auth/signup", json={**USER, "password": "x" * 73}).status_code == 422


def test_bad_tokens_rejected(client):
    client.post("/auth/signup", json=USER)
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)}, settings.jwt_secret, algorithm="HS256"
    )
    forged = jwt.encode({"sub": "1"}, "x" * 32, algorithm="HS256")
    assert client.get("/auth/me").status_code == 401
    for token in (expired, forged, "garbage"):
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_repeated_failures_lock_the_account(client):
    client.post("/auth/signup", json=USER)
    client.post("/auth/signup", json={**USER, "username": "other", "email": "other@example.com"})
    for _ in range(rate_limit.MAX_FAILURES_PER_ACCOUNT):
        assert login(client, password="wrong-password").status_code == 401
    locked = login(client)  # even the right password is refused while locked
    assert locked.status_code == 429 and "Retry-After" in locked.headers
    assert login(client, username="other").status_code == 200  # other accounts are unaffected


def test_success_clears_earlier_failures(client):
    client.post("/auth/signup", json=USER)
    for _ in range(rate_limit.MAX_FAILURES_PER_ACCOUNT - 1):
        login(client, password="wrong-password")
    assert login(client).status_code == 200
    for _ in range(rate_limit.MAX_FAILURES_PER_ACCOUNT - 1):
        login(client, password="wrong-password")
    assert login(client).status_code == 200

from bson import ObjectId
from datetime import datetime, timezone


def test_register_new_user(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "MyPass123",
        "full_name": "New User",
    }
    res = client.post("/auth/register", json=payload)
    body = res.json()
    assert body["code"] == 201
    assert "user" in body


def test_login_registered_user(client):
    # create user directly in the fake collection to avoid calling register endpoint
    from app.config import database as db
    import bcrypt as _bcrypt

    uid = ObjectId()
    hashed = _bcrypt.hashpw(b"Pwd12345", _bcrypt.gensalt()).decode("utf-8")
    db.user_collection.insert_one({
        "_id": uid,
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": hashed,
        "created_at": datetime.now(timezone.utc),
    })

    res = client.post("/auth/login", json={"identifier": "loginuser", "password": "Pwd12345"})
    body = res.json()
    assert body["code"] == 200
    assert "access_token" in body


def test_refresh_token_flow(client):
    # generate refresh token directly and call refresh endpoint
    from app.utils.jwt import create_refresh_token

    refresh = create_refresh_token(subject=str(client.test_user_id))
    res2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    body2 = res2.json()
    assert body2["code"] == 200
    assert "access_token" in body2


def test_forgot_password_endpoint(client):
    res = client.post("/auth/forgot-password", json={"email": "test@example.com"})
    body = res.json()
    assert body["code"] == 200
    assert "data" in body


def test_reset_password_endpoint(client):
    from app.utils.jwt import create_password_reset_token

    token = create_password_reset_token(subject=str(client.test_user_id), email="test@example.com")
    res2 = client.post("/auth/reset-password", json={"token": token, "new_password": "newpass"})
    body2 = res2.json()
    assert body2["code"] == 200


def test_register_conflict(client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "pass",
        "full_name": "x",
    }
    res = client.post("/auth/register", json=payload)
    assert res.json()["code"] == 409


def test_invalid_login(client):
    res2 = client.post("/auth/login", json={"identifier": "testuser", "password": "wrong"})
    assert res2.json()["code"] == 401

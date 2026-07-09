"""Auth endpoints: register, login, current user, and rejection paths."""


def test_register_returns_token(client):
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["access_token"]


def test_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 409


def test_login_and_me(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123", "name": "Al"})
    r = client.post("/api/auth/login", data={"username": "a@b.com", "password": "password123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.com"


def test_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    r = client.post("/api/auth/login", data={"username": "a@b.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_protected_route_requires_auth(client):
    assert client.get("/api/consumption/today").status_code == 401

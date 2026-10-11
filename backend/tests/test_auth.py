import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    payload = {"email": "test@example.com", "username": "testuser", "password": "secret123"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "viewer"

    resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "secret123"})
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_duplicate_register(client):
    payload = {"email": "dup@example.com", "username": "dupuser", "password": "pass"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_me_endpoint(client):
    await client.post(
        "/auth/register",
        json={"email": "me@example.com", "username": "meuser", "password": "pass"},
    )
    login = await client.post("/auth/login", json={"email": "me@example.com", "password": "pass"})
    token = login.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_protected_requires_auth(client):
    resp = await client.get("/pipeline/runs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_requires_admin_role(client):
    await client.post(
        "/auth/register",
        json={"email": "viewer@example.com", "username": "vieweruser", "password": "pass"},
    )
    login = await client.post("/auth/login", json={"email": "viewer@example.com", "password": "pass"})
    token = login.json()["access_token"]
    resp = await client.get("/admin/alerts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

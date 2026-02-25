"""
Integration tests — full auth flow against a real (test) PostgreSQL DB.

Requirements:
  - TEST_DATABASE_URL env var pointing at a clean test database
  - Redis running at REDIS_URL (from .env)

Run with:
  pytest tests/integration/ -m integration
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from tests.conftest import make_user

# ─── Helpers ──────────────────────────────────────────────────────────────────
_BASE = "/auth"

VALID_PASSWORD = "Integrate@1!"
REG_PAYLOAD = {
    "email": "integ@donehr.com",
    "password": VALID_PASSWORD,
    "confirm_password": VALID_PASSWORD,
    "full_name": "Integration User",
    "role": "candidate",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── POST /auth/register → 201 ────────────────────────────────────────────────
@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_returns_201(client: AsyncClient):
    with patch("app.tasks.email_tasks.send_verification_email") as mock_task:
        mock_task.delay = MagicMock()
        resp = await client.post(f"{_BASE}/register", json=REG_PAYLOAD)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == REG_PAYLOAD["email"]
    assert body["role"] == "candidate"
    assert body["is_verified"] is False


# ─── POST /auth/login (before verification) → 403 ─────────────────────────────
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_before_verification_returns_403(client: AsyncClient):
    # Register
    with patch("app.tasks.email_tasks.send_verification_email") as m:
        m.delay = MagicMock()
        await client.post(f"{_BASE}/register", json=REG_PAYLOAD)

    resp = await client.post(
        f"{_BASE}/login",
        json={"email": REG_PAYLOAD["email"], "password": VALID_PASSWORD},
    )
    assert resp.status_code == 403


# ─── Full happy-path flow ─────────────────────────────────────────────────────
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient, db_session):
    unique_email = f"flow_{uuid.uuid4().hex[:8]}@donehr.com"
    payload = {**REG_PAYLOAD, "email": unique_email}

    # 1. Register
    with patch("app.tasks.email_tasks.send_verification_email") as m:
        m.delay = MagicMock()
        reg_resp = await client.post(f"{_BASE}/register", json=payload)
    assert reg_resp.status_code == 201

    # 2. Manually mark email verified in test DB (simulates clicking link)
    await db_session.execute(
        text("UPDATE users SET is_verified = true WHERE email = :email"),
        {"email": unique_email},
    )
    await db_session.flush()

    # 3. Login → 200 with tokens
    with patch("app.core.redis_client.is_token_blacklisted", AsyncMock(return_value=False)):
        login_resp = await client.post(
            f"{_BASE}/login",
            json={"email": unique_email, "password": VALID_PASSWORD},
        )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert tokens["role"] == "candidate"

    # 4. GET /auth/me with token → 200
    with patch("app.core.redis_client.is_token_blacklisted", AsyncMock(return_value=False)):
        me_resp = await client.get(
            f"{_BASE}/me",
            headers=_auth_header(access_token),
        )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

    # 5. POST /auth/refresh → new access token
    with patch("app.core.redis_client.is_token_blacklisted", AsyncMock(return_value=False)), \
         patch("app.core.redis_client.blacklist_token", AsyncMock()):
        refresh_resp = await client.post(
            f"{_BASE}/refresh",
            json={"refresh_token": refresh_token},
        )
    assert refresh_resp.status_code == 200
    new_access = refresh_resp.json()["access_token"]
    assert new_access != access_token  # rotated

    # 6. POST /auth/logout → 200
    with patch("app.core.redis_client.blacklist_token", AsyncMock()):
        logout_resp = await client.post(
            f"{_BASE}/logout",
            headers=_auth_header(new_access),
        )
    assert logout_resp.status_code == 200

    # 7. Use the logged-out token → 401 (blacklisted)
    with patch("app.core.redis_client.is_token_blacklisted", AsyncMock(return_value=True)):
        revoked_resp = await client.get(
            f"{_BASE}/me",
            headers=_auth_header(new_access),
        )
    assert revoked_resp.status_code == 401


# ─── Wrong credentials ────────────────────────────────────────────────────────
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient, db_session):
    unique_email = f"wrong_{uuid.uuid4().hex[:8]}@donehr.com"
    payload = {**REG_PAYLOAD, "email": unique_email}

    with patch("app.tasks.email_tasks.send_verification_email") as m:
        m.delay = MagicMock()
        await client.post(f"{_BASE}/register", json=payload)

    await db_session.execute(
        text("UPDATE users SET is_verified = true WHERE email = :email"),
        {"email": unique_email},
    )
    await db_session.flush()

    resp = await client.post(
        f"{_BASE}/login",
        json={"email": unique_email, "password": "WrongPassword@1!"},
    )
    assert resp.status_code == 401


# ─── Duplicate registration ───────────────────────────────────────────────────
@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_register_returns_409(client: AsyncClient):
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@donehr.com"
    payload = {**REG_PAYLOAD, "email": unique_email}

    with patch("app.tasks.email_tasks.send_verification_email") as m:
        m.delay = MagicMock()
        r1 = await client.post(f"{_BASE}/register", json=payload)
        r2 = await client.post(f"{_BASE}/register", json=payload)

    assert r1.status_code == 201
    assert r2.status_code == 409

# Коротко: тести перевіряють сценарії модуля автентифікації.

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.storage[key] = value

    async def get(self, key: str) -> str | None:
        return self.storage.get(key)

    async def delete(self, key: str) -> None:
        self.storage.pop(key, None)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    redis = FakeRedis()
    monkeypatch.setattr("app.services.auth_service.get_redis", lambda: redis)
    return redis


@pytest.mark.asyncio
async def test_register_creates_client_and_stores_session(db_session, fake_redis: FakeRedis):
    service = AuthService(db_session)

    result = await service.register(
        RegisterRequest(
            email="NEWCLIENT@example.com",
            password="Password123!",
            first_name="  New ",
            last_name=" Client  ",
        )
    )

    user = result.public_payload.user
    assert user.email == "newclient@example.com"
    assert user.role == UserRole.CLIENT
    assert user.first_name == "New"
    assert user.last_name == "Client"

    access_payload = jwt.decode(
        result.cookies.access_token, settings.jwt_secret_key, algorithms=["HS256"]
    )
    refresh_payload = jwt.decode(
        result.cookies.refresh_token, settings.jwt_refresh_secret_key, algorithms=["HS256"]
    )

    assert access_payload["sub"] == user.id
    assert refresh_payload["sub"] == user.id
    assert access_payload["sid"] == refresh_payload["sid"]
    assert fake_redis.storage[settings.session_key(access_payload["sid"])] == user.id


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(db_session, fake_redis: FakeRedis):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(
            email="login-client@example.com",
            password="Password123!",
            first_name="Login",
            last_name="Client",
        )
    )

    with pytest.raises(HTTPException) as error:
        await service.login(
            LoginRequest(email="login-client@example.com", password="WrongPassword123!")
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_rotates_session_and_invalidates_previous_one(db_session, fake_redis: FakeRedis):
    service = AuthService(db_session)
    auth_result = await service.register(
        RegisterRequest(
            email="refresh-client@example.com",
            password="Password123!",
            first_name="Refresh",
            last_name="Client",
        )
    )

    old_payload = jwt.decode(
        auth_result.cookies.refresh_token, settings.jwt_refresh_secret_key, algorithms=["HS256"]
    )
    request = SimpleNamespace(cookies={settings.refresh_cookie_name: auth_result.cookies.refresh_token})

    refreshed = await service.refresh(request)

    new_payload = jwt.decode(
        refreshed.cookies.refresh_token, settings.jwt_refresh_secret_key, algorithms=["HS256"]
    )

    assert new_payload["sub"] == old_payload["sub"]
    assert new_payload["sid"] != old_payload["sid"]
    assert settings.session_key(old_payload["sid"]) not in fake_redis.storage
    assert fake_redis.storage[settings.session_key(new_payload["sid"])] == old_payload["sub"]


@pytest.mark.asyncio
async def test_logout_deletes_session_from_refresh_cookie(db_session, fake_redis: FakeRedis):
    admin = User(
        email="admin-logout@example.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Logout",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.commit()

    service = AuthService(db_session)
    auth_result = await service._issue_auth_payload(admin)
    payload = jwt.decode(
        auth_result.cookies.refresh_token, settings.jwt_refresh_secret_key, algorithms=["HS256"]
    )
    session_key = settings.session_key(payload["sid"])
    assert session_key in fake_redis.storage

    request = SimpleNamespace(
        cookies={
            settings.refresh_cookie_name: auth_result.cookies.refresh_token,
            settings.access_cookie_name: "",
        }
    )
    await service.logout(request)

    assert session_key not in fake_redis.storage

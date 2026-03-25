# Коротко: тести перевіряють сценарії модуля infra helpers.

import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api import deps
from app.core.cookies import AuthCookies, clear_auth_cookies, set_auth_cookies
from app.core.logging import RequestIdFilter
from app.core.request_context import generate_request_id, get_request_id, set_request_id
from app.main import (
    _request_id,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.csrf import CSRFMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.models.user import UserRole


def make_request(path: str = "/", method: str = "GET", headers=None, cookies=None) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": headers or [],
            "cookies": cookies or {},
            "state": {},
            "client": ("127.0.0.1", 1234),
        }
    )


@pytest.mark.asyncio
async def test_dependency_helpers(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.storage = {"auth:session:test-session": "user-1"}
            self.expired = []
            self.count = 0

        async def get(self, key):
            return self.storage.get(key)

        async def expire(self, key, seconds):
            self.expired.append((key, seconds))

        async def incr(self, key):
            self.count += 1
            return self.count

    class FakeRepo:
        def __init__(self, db):
            self.db = db

        async def get_by_id(self, user_id):
            return SimpleNamespace(
                id=user_id,
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                phone=None,
                is_verified=True,
                created_at=SimpleNamespace(),
                updated_at=SimpleNamespace(),
            )

    redis = FakeRedis()
    monkeypatch.setattr(deps, "decode_token", lambda token, secret: {"sub": "user-1", "sid": "test-session", "role": "ADMIN"})
    monkeypatch.setattr(deps, "get_redis", lambda: redis)
    monkeypatch.setattr(deps, "UserRepository", FakeRepo)

    request = make_request(headers=[], cookies={})
    current_user = await deps.get_current_user(request, object(), "token")
    assert current_user.id == "user-1"
    assert request.state.session_id == "test-session"
    assert redis.expired

    allowed = deps.require_roles(UserRole.ADMIN)
    assert (await allowed(current_user)).role == UserRole.ADMIN

    denied = deps.require_roles(UserRole.CLIENT)
    with pytest.raises(HTTPException):
        await denied(current_user)

    limiter = deps.rate_limit("auth", 1, 60)
    await limiter(make_request())
    with pytest.raises(HTTPException):
        await limiter(make_request())


def test_cookie_helpers_and_request_context():
    response = Response()
    cookies = AuthCookies("access-token", "refresh-token", "csrf-token")
    set_auth_cookies(response, cookies)
    assert "access-token" in response.headers.get("set-cookie", "")

    response = Response()
    clear_auth_cookies(response)
    assert "Max-Age=0" in response.headers.get("set-cookie", "")

    request_id = generate_request_id()
    set_request_id(request_id)
    assert get_request_id() == request_id

    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    assert RequestIdFilter().filter(record) is True
    assert record.request_id == request_id


def test_middleware_and_exception_handlers():
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)
    test_app.add_middleware(CSRFMiddleware)

    @test_app.get("/ping")
    async def ping():
        return {"ok": True}

    @test_app.post("/secure")
    async def secure():
        return {"ok": True}

    @test_app.post("/auth/login")
    async def login():
        return {"ok": True}

    client = TestClient(test_app)

    response = client.get("/ping", headers={"X-Request-ID": "req-123"})
    assert response.headers["X-Request-ID"] == "req-123"

    forbidden = client.post("/secure")
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "csrf_validation_failed"

    allowed = client.post("/secure", cookies={"fcms_csrf_token": "match"}, headers={"X-CSRF-Token": "match"})
    assert allowed.status_code == 200

    auth_allowed = client.post("/auth/login")
    assert auth_allowed.status_code == 200

    request = make_request()
    request.state.request_id = "req-1"
    assert _request_id(request) == "req-1"


@pytest.mark.asyncio
async def test_exception_handlers():
    request = make_request()
    request.state.request_id = "req-1"

    http_response = await http_exception_handler(request, HTTPException(status_code=400, detail="Bad"))
    assert isinstance(http_response, JSONResponse)
    assert http_response.body == b'{"detail":"Bad","code":"http_error","request_id":"req-1"}'

    validation_response = await validation_exception_handler(
        request,
        RequestValidationError([{"loc": ("body", "email"), "msg": "field required", "type": "missing"}]),
    )
    assert validation_response.status_code == 422

    unhandled_response = await unhandled_exception_handler(request, RuntimeError("boom"))
    assert unhandled_response.status_code == 500
    assert b"internal_server_error" in unhandled_response.body

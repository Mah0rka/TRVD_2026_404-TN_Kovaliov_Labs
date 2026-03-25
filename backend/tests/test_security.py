# Тести перевіряють ключові сценарії цього модуля.

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


# Перевіряє, що password hash roundtrip працює коректно.
def test_password_hash_roundtrip():
    password = "super-secret-password"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


# Перевіряє, що create access token payload працює коректно.
def test_create_access_token_payload():
    token = create_access_token("user-1", "CLIENT", "session-1")
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

    assert payload["sub"] == "user-1"
    assert payload["role"] == "CLIENT"
    assert payload["sid"] == "session-1"
    assert payload["type"] == "access"


# Перевіряє, що create refresh token payload працює коректно.
def test_create_refresh_token_payload():
    token = create_refresh_token("user-1", "CLIENT", "session-1")
    payload = jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=["HS256"])

    assert payload["sub"] == "user-1"
    assert payload["role"] == "CLIENT"
    assert payload["sid"] == "session-1"
    assert payload["type"] == "refresh"

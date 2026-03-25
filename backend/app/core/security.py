# Модуль зберігає спільну інфраструктурну логіку застосунку.

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from argon2 import PasswordHasher
from jose import jwt

from app.core.config import settings

password_hasher = PasswordHasher()


# Хешує пароль перед збереженням у базі даних.
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# Порівнює введений пароль із збереженим хешем.
def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


# Формує короткоживучий access token для активної сесії.
def create_access_token(subject: str, role: str, session_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "sid": session_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


# Формує refresh token для оновлення сесії без повторного логіну.
def create_refresh_token(subject: str, role: str, session_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "sid": session_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_token_expire_days)).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret_key, algorithm="HS256")


# Декодує та перевіряє JWT токен.
def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])

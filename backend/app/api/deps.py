# Модуль збирає залежності FastAPI для сесії, авторизації та rate limit.

from collections.abc import AsyncGenerator

from fastapi import Cookie, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


# Видає асинхронну сесію бази даних на час обробки запиту.
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# Дістає поточного користувача із cookie-сесії та перевіряє її актуальність.
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    access_token: str | None = Cookie(default=None, alias=settings.access_cookie_name),
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = decode_token(access_token, settings.jwt_secret_key)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    role = payload.get("role")
    if not user_id or not session_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token payload")

    redis = get_redis()
    session_key = settings.session_key(session_id)
    stored_user_id = await redis.get(session_key)
    if stored_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    if role in {UserRole.ADMIN.value, UserRole.OWNER.value}:
        await redis.expire(session_key, settings.admin_idle_timeout_seconds)

    repository = UserRepository(db)
    user = await repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    request.state.current_user = user
    request.state.session_id = session_id
    return user


# Створює залежність FastAPI, яка пропускає лише користувачів з потрібними ролями.
def require_roles(*roles: UserRole):
    # Перевіряє роль поточного користувача перед доступом до захищеного маршруту.
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


# Створює залежність FastAPI для обмеження частоти запитів у вибраному scope.
def rate_limit(scope: str, limit: int, window_seconds: int):
    # Рахує запити клієнта в Redis і блокує перевищення заданого ліміту.
    async def dependency(request: Request) -> None:
        redis = get_redis()
        client_host = request.client.host if request.client else "unknown"
        key = f"ratelimit:{scope}:{client_host}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return dependency

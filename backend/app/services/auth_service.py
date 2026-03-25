# Коротко: сервіс містить бізнес-логіку модуля автентифікації.

from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.config import settings
from app.core.cookies import AuthCookies
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthPayload, AuthResult, LoginRequest, RegisterRequest
from app.schemas.user import UserRead


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.redis = get_redis()

    async def register(self, payload: RegisterRequest, request: Request | None = None) -> AuthResult:
        existing_user = await self.repository.get_by_email(payload.email)
        if existing_user:
            log_audit_event("auth.register", "failed", email=payload.email.lower(), reason="email_exists")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            role=UserRole.CLIENT,
            is_verified=False,
        )
        created_user = await self.repository.create(user)
        log_audit_event("auth.register", "success", email=created_user.email, user_id=created_user.id)
        return await self._issue_auth_payload(created_user)

    async def login(self, payload: LoginRequest, request: Request | None = None) -> AuthResult:
        user = await self.repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            log_audit_event("auth.login", "failed", email=payload.email.lower(), reason="invalid_credentials")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        auth_result = await self._issue_auth_payload(user)
        log_audit_event("auth.login", "success", email=user.email, user_id=user.id)
        return auth_result

    async def refresh(self, request: Request) -> AuthResult:
        refresh_token = request.cookies.get(settings.refresh_cookie_name)
        if not refresh_token:
            log_audit_event("auth.refresh", "failed", reason="missing_token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing")

        try:
            payload = decode_token(refresh_token, settings.jwt_refresh_secret_key)
        except JWTError as exc:
            log_audit_event("auth.refresh", "failed", reason="invalid_token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        user_id = payload.get("sub")
        role = payload.get("role")
        session_id = payload.get("sid")
        token_type = payload.get("type")

        if not user_id or not role or not session_id or token_type != "refresh":
            log_audit_event("auth.refresh", "failed", reason="invalid_payload")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

        session_key = settings.session_key(session_id)
        stored_user_id = await self.redis.get(session_key)
        if stored_user_id != user_id:
            log_audit_event("auth.refresh", "failed", user_id=user_id, session_id=session_id, reason="session_expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired")

        user = await self.repository.get_by_id(user_id)
        if not user:
            log_audit_event("auth.refresh", "failed", user_id=user_id, session_id=session_id, reason="user_missing")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        await self.redis.delete(session_key)
        auth_result = await self._issue_auth_payload(user)
        log_audit_event("auth.refresh", "success", user_id=user.id, session_id=session_id)
        return auth_result

    async def logout(self, request: Request) -> None:
        access_token = request.cookies.get(settings.access_cookie_name)
        payload = None
        if access_token:
            try:
                payload = decode_token(access_token, settings.jwt_secret_key)
            except JWTError:
                payload = None

        if payload is None:
            refresh_token = request.cookies.get(settings.refresh_cookie_name)
            if not refresh_token:
                log_audit_event("auth.logout", "success", reason="no_session")
                return
            try:
                payload = decode_token(refresh_token, settings.jwt_refresh_secret_key)
            except JWTError:
                log_audit_event("auth.logout", "success", reason="invalid_refresh_cookie")
                return

        session_id = payload.get("sid")
        if session_id:
            await self.redis.delete(settings.session_key(session_id))
        log_audit_event("auth.logout", "success", user_id=payload.get("sub"), session_id=session_id)

    async def _issue_auth_payload(self, user: User) -> AuthResult:
        session_id = str(uuid4())
        session_ttl = (
            settings.admin_idle_timeout_seconds
            if user.role in {UserRole.ADMIN, UserRole.OWNER}
            else settings.refresh_token_expire_seconds
        )

        await self.redis.set(settings.session_key(session_id), user.id, ex=session_ttl)

        access_token = create_access_token(user.id, user.role.value, session_id)
        refresh_token = create_refresh_token(user.id, user.role.value, session_id)
        csrf_token = token_urlsafe(32)

        public_payload = AuthPayload(user=UserRead.model_validate(user))
        cookies = AuthCookies(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
        return AuthResult(public_payload=public_payload, cookies=cookies)

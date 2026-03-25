# Коротко: маршрут обробляє HTTP-запити для модуля автентифікації.

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, rate_limit
from app.models.user import User
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.config import settings
from app.schemas.auth import AuthPayload, LoginRequest, RefreshResponse, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthPayload, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    _: None = Depends(
        rate_limit("auth:register", settings.auth_register_rate_limit, settings.auth_rate_limit_window_seconds)
    ),
    db: AsyncSession = Depends(get_db_session),
) -> AuthPayload:
    service = AuthService(db)
    auth_payload = await service.register(payload, request)
    set_auth_cookies(response, auth_payload.cookies)
    return auth_payload.public_payload


@router.post("/login", response_model=AuthPayload)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    _: None = Depends(
        rate_limit("auth:login", settings.auth_login_rate_limit, settings.auth_rate_limit_window_seconds)
    ),
    db: AsyncSession = Depends(get_db_session),
) -> AuthPayload:
    service = AuthService(db)
    auth_payload = await service.login(payload, request)
    set_auth_cookies(response, auth_payload.cookies)
    return auth_payload.public_payload


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    _: None = Depends(
        rate_limit("auth:refresh", settings.auth_refresh_rate_limit, settings.auth_rate_limit_window_seconds)
    ),
    db: AsyncSession = Depends(get_db_session),
) -> RefreshResponse:
    service = AuthService(db)
    auth_payload = await service.refresh(request)
    set_auth_cookies(response, auth_payload.cookies)
    return RefreshResponse(user=auth_payload.public_payload.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = AuthService(db)
    await service.logout(request)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

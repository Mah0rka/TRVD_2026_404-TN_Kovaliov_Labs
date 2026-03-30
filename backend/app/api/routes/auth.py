# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_PAYLOAD_EXAMPLE,
    AUTH_REQUIRED_RESPONSE,
    RATE_LIMIT_RESPONSE,
    REFRESH_RESPONSE_EXAMPLE,
    VALIDATION_ERROR_RESPONSE,
    conflict_response,
    merge_responses,
    no_content_response,
    response_example,
)
from app.api.deps import get_current_user, get_db_session, rate_limit
from app.models.user import User
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.config import settings
from app.schemas.auth import AuthPayload, LoginRequest, RefreshResponse, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


# Реєструє користувача та запускає видачу сесійних cookies.
@router.post(
    "/register",
    response_model=AuthPayload,
    status_code=status.HTTP_201_CREATED,
    summary="Зареєструвати нового користувача",
    description=(
        "Створює обліковий запис, одразу відкриває сесію та повертає профіль користувача. "
        "Перший зареєстрований користувач у системі автоматично отримує роль OWNER."
    ),
    responses=merge_responses(
        {201: response_example("Користувача успішно зареєстровано.", AUTH_PAYLOAD_EXAMPLE)},
        conflict_response("Email уже зайнятий іншим користувачем.", "Email already registered"),
        RATE_LIMIT_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
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


# Перевіряє облікові дані й відкриває нову користувацьку сесію.
@router.post(
    "/login",
    response_model=AuthPayload,
    summary="Увійти в систему",
    description=(
        "Перевіряє email і пароль, створює нову cookie-сесію та повертає профіль "
        "авторизованого користувача."
    ),
    responses=merge_responses(
        {200: response_example("Вхід успішний, сесію створено.", AUTH_PAYLOAD_EXAMPLE)},
        {
            401: response_example(
                "Невірні облікові дані або сесію не вдалося створити.",
                {
                    "detail": "Invalid credentials",
                    "code": "http_error",
                    "request_id": "req_01HV7JQ4KQ6P1H9R5V2M8C7D3F",
                },
            )
        },
        RATE_LIMIT_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
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


# Оновлює сесію за refresh token і перевидає auth cookies.
@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Оновити cookie-сесію",
    description=(
        "Зчитує refresh token із cookie, перевидає access/refresh cookie та повертає "
        "актуальний профіль користувача."
    ),
    responses=merge_responses(
        {200: response_example("Сесію успішно оновлено.", REFRESH_RESPONSE_EXAMPLE)},
        {
            401: response_example(
                "Refresh token відсутній, прострочений або більше не прив'язаний до активної сесії.",
                {
                    "detail": "Refresh token is missing",
                    "code": "http_error",
                    "request_id": "req_01HV7JQ4KQ6P1H9R5V2M8C7D3F",
                },
            )
        },
        RATE_LIMIT_RESPONSE,
    ),
)
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


# Закриває активну сесію та очищає cookies авторизації.
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вийти з поточної сесії",
    description=(
        "Закриває активну серверну сесію, якщо вона існує, і очищає auth cookie. "
        "Маршрут ідемпотентний: повторний виклик теж повертає 204."
    ),
    responses={204: no_content_response("Сесію закрито або cookie вже були очищені.")},
)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = AuthService(db)
    await service.logout(request)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response)
    return response


# Повертає профіль поточного авторизованого користувача.
@router.get(
    "/me",
    response_model=UserRead,
    summary="Отримати поточного користувача",
    description="Повертає профіль користувача, який зараз авторизований через cookie-сесію.",
    responses=merge_responses(
        {200: response_example("Поточний профіль користувача.", AUTH_PAYLOAD_EXAMPLE["user"])},
        AUTH_REQUIRED_RESPONSE,
    ),
)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

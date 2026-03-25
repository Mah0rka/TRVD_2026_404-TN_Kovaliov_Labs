# Модуль зберігає спільну інфраструктурну логіку застосунку.

from dataclasses import dataclass

from fastapi import Response

from app.core.config import settings


@dataclass(slots=True)
class AuthCookies:
    access_token: str
    refresh_token: str
    csrf_token: str


# Записує access, refresh і CSRF cookies у відповідь сервера.
def set_auth_cookies(response: Response, cookies: AuthCookies) -> None:
    response.set_cookie(
        key=settings.access_cookie_name,
        value=cookies.access_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=cookies.refresh_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.refresh_token_expire_seconds,
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=cookies.csrf_token,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.refresh_token_expire_seconds,
        domain=settings.cookie_domain,
        path="/",
    )


# Очищає auth cookies під час виходу користувача.
def clear_auth_cookies(response: Response) -> None:
    for cookie_name in (settings.access_cookie_name, settings.refresh_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(key=cookie_name, domain=settings.cookie_domain, path="/")

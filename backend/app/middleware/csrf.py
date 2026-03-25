# Коротко: middleware виконує службову логіку для модуля CSRF-захисту.

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.request_context import generate_request_id, set_request_id


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            request_id = request.headers.get("X-Request-ID") or generate_request_id()
            set_request_id(request_id)
            request.state.request_id = request_id

        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        if request.url.path in {"/auth/login", "/auth/register", "/auth/refresh"}:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF validation failed",
                    "code": "csrf_validation_failed",
                    "request_id": request_id,
                },
            )

        return await call_next(request)

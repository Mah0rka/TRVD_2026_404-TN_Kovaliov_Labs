# Файл містить допоміжну логіку для цього модуля.

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.docs import API_DESCRIPTION, API_SUMMARY, OPENAPI_TAGS
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.csrf import CSRFMiddleware
from app.middleware.request_context import RequestContextMiddleware


configure_logging()
logger = logging.getLogger(__name__)
RESERVED_FRONTEND_PREFIXES = {
    "auth",
    "bookings",
    "docs",
    "health",
    "openapi.json",
    "payments",
    "public",
    "redoc",
    "reports",
    "schedules",
    "subscriptions",
    "users",
}

app = FastAPI(
    title=settings.app_name,
    summary=API_SUMMARY,
    description=API_DESCRIPTION,
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CSRFMiddleware)
app.include_router(api_router)


# Повертає шлях до зібраного фронтенду, якщо його можна віддавати з бекенду.
def frontend_dist_dir() -> Path | None:
    if not settings.serve_frontend or not settings.frontend_dist_path:
        return None

    dist_dir = Path(settings.frontend_dist_path).resolve()
    if not dist_dir.is_dir():
        logger.warning("Frontend dist path is missing", extra={"frontend_dist_path": str(dist_dir)})
        return None

    return dist_dir


# Визначає, який файл фронтенду слід повернути для запитаного шляху.
def resolve_frontend_file(dist_dir: Path, requested_path: str) -> Path | None:
    normalized_path = requested_path.strip("/")
    candidate = (dist_dir / normalized_path).resolve() if normalized_path else dist_dir / "index.html"

    if candidate.is_file() and (candidate == dist_dir / "index.html" or dist_dir in candidate.parents):
        return candidate

    first_segment = normalized_path.split("/", 1)[0] if normalized_path else ""
    if first_segment in RESERVED_FRONTEND_PREFIXES:
        return None

    if normalized_path and "." in Path(normalized_path).name:
        return None

    return dist_dir / "index.html"


# Дістає ідентифікатор поточного запиту для логування та відповідей.
def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


# Уніфікує HTTP-помилки у спільний формат відповіді API.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "http_error",
            "request_id": _request_id(request),
        },
    )


# Перетворює помилки валідації на зрозумілу відповідь API.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "code": "validation_error",
            "request_id": _request_id(request),
            "errors": jsonable_encoder(exc.errors()),
        },
    )


# Логує неочікувану помилку та повертає безпечну відповідь сервера.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "internal_server_error",
            "request_id": _request_id(request),
        },
    )


# Віддає файл фронтенду для кореневого маршруту або SPA-шляху.
@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_app(full_path: str = ""):
    dist_dir = frontend_dist_dir()
    if dist_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    response_file = resolve_frontend_file(dist_dir, full_path)
    if response_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return FileResponse(response_file)

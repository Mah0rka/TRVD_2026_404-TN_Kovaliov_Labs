# Модуль зберігає спільну інфраструктурну логіку застосунку.

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Визначає джерело змінних середовища та ігнорує зайві ключі в `.env`.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Базові параметри застосунку; інфраструктурні URL мають приходити із середовища.
    app_name: str = "MotionLab API"
    app_env: str = "development"
    database_url: str
    redis_url: str

    # JWT-секрети теж обов'язкові: для них не лишаємо небезпечних fallback-значень.
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Параметри безпеки cookies і тривалості неактивної адмін-сесії.
    admin_idle_timeout_minutes: int = 30
    secure_cookies: bool = True
    cookie_domain: str | None = None

    # Сире значення для CORS з `.env`; нижче перетворюється на список origins.
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # Керування інфраструктурними діями під час старту застосунку.
    run_db_migrations: bool = True
    seed_demo_data: bool = False
    serve_frontend: bool = False
    frontend_dist_path: str | None = None

    # Обмеження частоти запитів для чутливих операцій автентифікації та підписок.
    auth_login_rate_limit: int = 5
    auth_register_rate_limit: int = 3
    auth_refresh_rate_limit: int = 10
    subscription_purchase_rate_limit: int = 5
    subscription_freeze_rate_limit: int = 10
    auth_rate_limit_window_seconds: int = 60

    # Горизонт наперед, на який матеріалізується розклад.
    schedule_materialization_horizon_days: int = 180

    # Імена cookies винесені в налаштування, щоб централізовано керувати ними.
    access_cookie_name: str = "fcms_access_token"
    refresh_cookie_name: str = "fcms_refresh_token"
    csrf_cookie_name: str = "fcms_csrf_token"

    # Обслуговує сценарій refresh token expire seconds.
    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60

    # Обслуговує сценарій admin idle timeout seconds.
    @property
    def admin_idle_timeout_seconds(self) -> int:
        return self.admin_idle_timeout_minutes * 60

    # Обслуговує сценарій cors origins.
    @property
    def cors_origins(self) -> list[str]:
        # Розбиває CSV-рядок з `.env` на чистий список origin-адрес.
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # Обслуговує сценарій session key.
    def session_key(self, session_id: str) -> str:
        # Формує стандартизований Redis-ключ для серверної сесії.
        return f"auth:session:{session_id}"

    # Перевіряє security defaults.
    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        # Небезпечні значення дозволені лише локально, щоб випадково не винести їх у production.
        insecure_values = {
            "change-me",
            "change-me-too",
            "super-secret-jwt-key",
            "super-secret-refresh-key",
            "local-dev-jwt-secret-change-me",
            "local-dev-refresh-secret-change-me",
        }

        if self.app_env != "development":
            if self.jwt_secret_key in insecure_values or self.jwt_refresh_secret_key in insecure_values:
                raise ValueError("JWT secrets must be overridden outside development")
            if not self.secure_cookies:
                raise ValueError("secure_cookies must stay enabled outside development")

        return self


# Створює та кешує обʼєкт налаштувань застосунку.
@lru_cache
def get_settings() -> Settings:
    # Кеш потрібен, щоб не перечитувати `.env` і не перевалідовувати конфіг при кожному виклику.
    return Settings()


# Експортує готовий singleton-конфіг для зручного імпорту в інших модулях.
settings = get_settings()

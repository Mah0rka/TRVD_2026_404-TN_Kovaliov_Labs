# Коротко: ядро містить інфраструктурну логіку для модуля конфігурації.

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MotionLab API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://root:password@localhost:5433/fcms"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me"
    jwt_refresh_secret_key: str = "change-me-too"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    admin_idle_timeout_minutes: int = 30
    secure_cookies: bool = True
    cookie_domain: str | None = None
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:5173")
    run_db_migrations: bool = True
    seed_demo_data: bool = False
    auth_login_rate_limit: int = 5
    auth_register_rate_limit: int = 3
    auth_refresh_rate_limit: int = 10
    subscription_purchase_rate_limit: int = 5
    subscription_freeze_rate_limit: int = 10
    auth_rate_limit_window_seconds: int = 60

    access_cookie_name: str = "fcms_access_token"
    refresh_cookie_name: str = "fcms_refresh_token"
    csrf_cookie_name: str = "fcms_csrf_token"

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60

    @property
    def admin_idle_timeout_seconds(self) -> int:
        return self.admin_idle_timeout_minutes * 60

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def session_key(self, session_id: str) -> str:
        return f"auth:session:{session_id}"

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Схеми задають валідацію вхідних даних і формат відповідей API.

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.docs import (
    AUTH_PAYLOAD_EXAMPLE,
    LOGIN_REQUEST_EXAMPLE,
    REFRESH_RESPONSE_EXAMPLE,
    REGISTER_REQUEST_EXAMPLE,
)
from app.core.cookies import AuthCookies
from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": REGISTER_REQUEST_EXAMPLE})

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)


class LoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": LOGIN_REQUEST_EXAMPLE})

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthPayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": AUTH_PAYLOAD_EXAMPLE})

    user: UserRead


class RefreshResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": REFRESH_RESPONSE_EXAMPLE})

    user: UserRead


@dataclass(slots=True)
class AuthResult:
    public_payload: AuthPayload
    cookies: AuthCookies

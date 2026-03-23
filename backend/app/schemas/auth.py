from dataclasses import dataclass

from pydantic import BaseModel, EmailStr, Field

from app.core.cookies import AuthCookies
from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthPayload(BaseModel):
    user: UserRead


class RefreshResponse(BaseModel):
    user: UserRead


@dataclass(slots=True)
class AuthResult:
    public_payload: AuthPayload
    cookies: AuthCookies

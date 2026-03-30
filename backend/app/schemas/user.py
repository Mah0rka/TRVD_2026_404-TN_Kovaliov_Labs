# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.docs import (
    USER_ADMIN_CREATE_EXAMPLE,
    USER_ADMIN_UPDATE_EXAMPLE,
    USER_EXAMPLE,
    USER_PROFILE_UPDATE_EXAMPLE,
)
from app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": USER_EXAMPLE})

    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    phone: str | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": USER_PROFILE_UPDATE_EXAMPLE})

    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=32)


class UserAdminCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": USER_ADMIN_CREATE_EXAMPLE})

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole = UserRole.CLIENT
    is_verified: bool = True


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": USER_ADMIN_UPDATE_EXAMPLE})

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole | None = None
    is_verified: bool | None = None

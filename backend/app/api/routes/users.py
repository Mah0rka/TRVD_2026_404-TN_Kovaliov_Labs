# Коротко: маршрут обробляє HTTP-запити для модуля користувачів.

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserProfileUpdate, UserRead
from app.services.user_service import UserService

router = APIRouter()


@router.get("/profile", response_model=UserRead)
async def profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/profile", response_model=UserRead)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(db)
    user = await service.update_profile(current_user, payload)
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
async def list_users(
    role: UserRole | None = Query(default=None),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[UserRead]:
    service = UserService(db)
    users = await service.list_users(role)
    return [UserRead.model_validate(user) for user in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserAdminCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(db)
    user = await service.create_user(payload)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserAdminUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(db)
    user = await service.update_user(user_id, payload)
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = UserService(db)
    await service.delete_user(current_user, user_id)

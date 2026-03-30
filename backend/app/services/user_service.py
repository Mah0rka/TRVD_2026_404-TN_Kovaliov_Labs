# Сервіс інкапсулює бізнес-правила та координує роботу репозиторіїв.

import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserListPage, UserProfileUpdate, UserRead


class UserService:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    # Повертає список користувачів з необовʼязковою фільтрацією за роллю.
    async def list_users(self, role: UserRole | None = None) -> list[User]:
        return await self.repository.list_all(role)

    # Повертає сторінку користувачів з метаданими пагінації.
    async def list_users_page(
        self,
        page: int,
        page_size: int,
        role: UserRole | None = None,
    ) -> UserListPage:
        total = await self.repository.count_filtered(role)
        users = await self.repository.list_page(page=page, page_size=page_size, role=role)
        total_pages = max(1, math.ceil(total / page_size)) if total else 1
        return UserListPage(
            items=[UserRead.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # Оновлює особисті дані поточного користувача.
    async def update_profile(self, user: User, payload: UserProfileUpdate) -> User:
        update_data = payload.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(user, field_name, value)
        return await self.repository.commit(user)

    # Створює користувача з адмінського інтерфейсу.
    async def create_user(self, payload: UserAdminCreate) -> User:
        existing_user = await self.repository.get_by_email(payload.email)
        if existing_user:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            phone=payload.phone.strip() if payload.phone else None,
            role=payload.role,
            is_verified=payload.is_verified,
        )
        return await self.repository.create(user)

    # Оновлює профіль користувача з адмінського інтерфейсу.
    async def update_user(self, user_id: str, payload: UserAdminUpdate) -> User:
        from fastapi import HTTPException, status

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_data = payload.model_dump(exclude_unset=True)
        email = update_data.get("email")
        if email and email.lower() != user.email:
            existing_user = await self.repository.get_by_email(email)
            if existing_user and existing_user.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
            user.email = email.lower()

        password = update_data.pop("password", None)
        if password:
            user.password_hash = hash_password(password)

        for field_name, value in update_data.items():
            if field_name == "email":
                continue
            if isinstance(value, str):
                value = value.strip()
            setattr(user, field_name, value)

        return await self.repository.commit(user)

    # Видаляє користувача з урахуванням захисту від небезпечних сценаріїв.
    async def delete_user(self, actor: User, user_id: str) -> None:
        from fastapi import HTTPException, status

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if actor.id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account",
            )

        if user.role == UserRole.OWNER:
            owners_count = await self.repository.count_by_role(UserRole.OWNER)
            if owners_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot delete the last owner account",
                )

        await self.repository.delete(user)

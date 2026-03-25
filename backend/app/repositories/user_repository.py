# Репозиторій ізолює читання та запис даних у базі.

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Повертає by email.
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    # Повертає by id.
    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    # Створює потрібні дані.
    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # Підраховує all.
    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())

    # Повертає список all.
    async def list_all(self, role: UserRole | None = None) -> list[User]:
        statement = select(User).order_by(User.created_at.desc())
        if role:
            statement = statement.where(User.role == role)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    # Обслуговує сценарій commit.
    async def commit(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # Підраховує by role.
    async def count_by_role(self, role: UserRole) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.role == role)
        )
        return int(result.scalar_one())

    # Видаляє потрібні дані.
    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_all(self, role: UserRole | None = None) -> list[User]:
        statement = select(User).order_by(User.created_at.desc())
        if role:
            statement = statement.where(User.role == role)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def commit(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user

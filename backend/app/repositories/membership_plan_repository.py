# Коротко: репозиторій інкапсулює доступ до даних для модуля membership plan repository.

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership_plan import MembershipPlan


class MembershipPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, active_only: bool = False, public_only: bool = False) -> list[MembershipPlan]:
        statement = select(MembershipPlan).order_by(MembershipPlan.sort_order.asc(), MembershipPlan.created_at.asc())
        if active_only:
            statement = statement.where(MembershipPlan.is_active.is_(True))
        if public_only:
            statement = statement.where(MembershipPlan.is_public.is_(True))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, plan_id: str) -> MembershipPlan | None:
        result = await self.session.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
        return result.scalar_one_or_none()

    async def create(self, plan: MembershipPlan) -> MembershipPlan:
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def delete(self, plan: MembershipPlan) -> None:
        await self.session.delete(plan)
        await self.session.commit()

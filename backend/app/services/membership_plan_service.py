# Сервіс інкапсулює бізнес-правила та координує роботу репозиторіїв.

from fastapi import HTTPException, status

from app.models.membership_plan import MembershipPlan
from app.repositories.membership_plan_repository import MembershipPlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.membership_plan import MembershipPlanCreate, MembershipPlanUpdate


class MembershipPlanService:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session) -> None:
        self.session = session
        self.repository = MembershipPlanRepository(session)
        self.subscription_repository = SubscriptionRepository(session)

    # Повертає список plans.
    async def list_plans(self, active_only: bool = False, public_only: bool = False) -> list[MembershipPlan]:
        return await self.repository.list_all(active_only=active_only, public_only=public_only)

    # Повертає plan.
    async def get_plan(self, plan_id: str) -> MembershipPlan:
        plan = await self.repository.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership plan not found")
        return plan

    # Створює plan.
    async def create_plan(self, payload: MembershipPlanCreate) -> MembershipPlan:
        plan = MembershipPlan(**payload.model_dump())
        return await self.repository.create(plan)

    # Оновлює plan.
    async def update_plan(self, plan_id: str, payload: MembershipPlanUpdate) -> MembershipPlan:
        plan = await self.get_plan(plan_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    # Видаляє plan.
    async def delete_plan(self, plan_id: str) -> None:
        plan = await self.get_plan(plan_id)
        linked_subscriptions = await self.subscription_repository.list_by_plan(plan_id)
        if linked_subscriptions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan is already used in subscriptions and cannot be deleted",
            )
        await self.repository.delete(plan)

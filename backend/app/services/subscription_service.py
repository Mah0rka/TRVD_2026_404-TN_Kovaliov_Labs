from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership_plan import MembershipPlan
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User
from app.schemas.subscription import SubscriptionManagementIssueRequest, SubscriptionManagementUpdate
from app.repositories.membership_plan_repository import MembershipPlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.payment_service import PaymentService


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SubscriptionRepository(session)
        self.plan_repository = MembershipPlanRepository(session)

    async def purchase(
        self,
        user_id: str,
        subscription_type: SubscriptionType | None = None,
        plan_id: str | None = None,
    ) -> Subscription:
        existing_subscriptions = await self.repository.list_by_user(user_id)
        if any(
            subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.FROZEN}
            for subscription in existing_subscriptions
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Finish or pause your current membership before purchasing a new one",
            )

        plan = await self._resolve_plan(
            plan_id=plan_id,
            subscription_type=subscription_type,
            require_public=True,
        )

        start_date = datetime.now(UTC)
        end_date = start_date + timedelta(days=plan.duration_days)
        payment_service = PaymentService(self.session)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            type=plan.type,
            start_date=start_date,
            end_date=end_date,
            total_visits=plan.visits_limit,
            remaining_visits=plan.visits_limit,
            status=SubscriptionStatus.ACTIVE,
        )
        payment = payment_service.build_plan_payment(user_id, plan)

        self.session.add_all([subscription, payment])
        await self.session.commit()
        return (await self.repository.get_by_id(subscription.id)) or subscription

    async def issue_for_management(
        self,
        actor_user_id: str,
        payload: SubscriptionManagementIssueRequest,
    ) -> Subscription:
        plan = await self._resolve_plan(
            plan_id=payload.plan_id,
            subscription_type=None,
            require_public=False,
        )
        user = await self.session.get(User, payload.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        start_date = payload.start_date or datetime.now(UTC)
        end_date = payload.end_date or (start_date + timedelta(days=plan.duration_days))
        total_visits = payload.total_visits if payload.total_visits is not None else plan.visits_limit
        remaining_visits = (
            payload.remaining_visits if payload.remaining_visits is not None else total_visits
        )

        subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            type=plan.type,
            start_date=start_date,
            end_date=end_date,
            status=payload.status,
            total_visits=total_visits,
            remaining_visits=remaining_visits,
            last_modified_by_id=actor_user_id,
            last_modified_at=datetime.now(UTC),
        )
        self._validate_management_update(subscription)
        self.session.add(subscription)
        await self.session.commit()
        return (await self.repository.get_by_id(subscription.id, include_deleted=True)) or subscription

    async def freeze(self, user_id: str, subscription_id: str, days: int) -> Subscription:
        subscription = await self.repository.get_by_id(subscription_id)
        if not subscription or subscription.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active subscriptions can be frozen")

        subscription.status = SubscriptionStatus.FROZEN
        subscription.end_date = subscription.end_date + timedelta(days=days)
        subscription.last_modified_by_id = user_id
        subscription.last_modified_at = datetime.now(UTC)
        await self.session.commit()
        return (await self.repository.get_by_id(subscription.id)) or subscription

    async def list_for_user(self, user_id: str) -> list[Subscription]:
        return await self.repository.list_by_user(user_id)

    async def list_for_management(
        self,
        *,
        user_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[Subscription]:
        return await self.repository.list_all(user_id=user_id, include_deleted=include_deleted)

    async def update_for_management(
        self,
        actor_user_id: str,
        subscription_id: str,
        payload: SubscriptionManagementUpdate,
    ) -> Subscription:
        subscription = await self.repository.get_by_id(subscription_id, include_deleted=True)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        if subscription.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deleted subscriptions cannot be edited",
            )

        updates = payload.model_dump(exclude_unset=True)

        if "plan_id" in updates:
            plan = await self._resolve_plan(
                plan_id=payload.plan_id,
                subscription_type=None,
                require_public=False,
            )
            subscription.plan_id = plan.id
            subscription.type = plan.type
            if "total_visits" not in updates:
                subscription.total_visits = plan.visits_limit
            if "remaining_visits" not in updates:
                subscription.remaining_visits = plan.visits_limit

        if "start_date" in updates:
            subscription.start_date = payload.start_date
        if "end_date" in updates:
            subscription.end_date = payload.end_date
        if "status" in updates:
            subscription.status = payload.status
        if "total_visits" in updates:
            subscription.total_visits = payload.total_visits
        if "remaining_visits" in updates:
            subscription.remaining_visits = payload.remaining_visits

        self._validate_management_update(subscription)
        subscription.last_modified_by_id = actor_user_id
        subscription.last_modified_at = datetime.now(UTC)
        await self.session.commit()
        return (await self.repository.get_by_id(subscription.id, include_deleted=True)) or subscription

    async def delete_for_management(self, actor_user_id: str, subscription_id: str) -> None:
        subscription = await self.repository.get_by_id(subscription_id, include_deleted=True)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        if subscription.deleted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription already deleted")

        now = datetime.now(UTC)
        subscription.deleted_by_id = actor_user_id
        subscription.deleted_at = now
        subscription.last_modified_by_id = actor_user_id
        subscription.last_modified_at = now
        await self.session.commit()

    async def restore_for_management(self, actor_user_id: str, subscription_id: str) -> Subscription:
        subscription = await self.repository.get_by_id(subscription_id, include_deleted=True)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        if not subscription.deleted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription is not deleted")

        now = datetime.now(UTC)
        subscription.deleted_by_id = None
        subscription.deleted_at = None
        subscription.restored_by_id = actor_user_id
        subscription.restored_at = now
        subscription.last_modified_by_id = actor_user_id
        subscription.last_modified_at = now
        if subscription.status == SubscriptionStatus.EXPIRED and subscription.end_date > now:
            subscription.status = SubscriptionStatus.ACTIVE
        await self.session.commit()
        return (await self.repository.get_by_id(subscription.id, include_deleted=True)) or subscription

    async def _resolve_plan(
        self,
        *,
        plan_id: str | None,
        subscription_type: SubscriptionType | None,
        require_public: bool,
    ) -> MembershipPlan:
        if plan_id:
            plan = await self.plan_repository.get_by_id(plan_id)
            if not plan or not plan.is_active:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership plan not found")
            if require_public and not plan.is_public:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership plan not found")
            return plan

        if subscription_type:
            plans = await self.plan_repository.list_all(active_only=True, public_only=require_public)
            matching = next((plan for plan in plans if plan.type == subscription_type), None)
            if matching:
                return matching

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership plan is required")

    def _validate_management_update(self, subscription: Subscription) -> None:
        if subscription.start_date > subscription.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription end date must be after start date",
            )

        if subscription.total_visits is not None and subscription.remaining_visits is not None:
            if subscription.remaining_visits > subscription.total_visits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Remaining visits cannot exceed total visits",
                )

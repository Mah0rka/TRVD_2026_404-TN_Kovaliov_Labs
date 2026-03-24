from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.membership_plan import MembershipPlan
from app.models.subscription import SubscriptionType
from app.repositories.payment_repository import PaymentRepository

SUBSCRIPTION_PRICES = {
    SubscriptionType.MONTHLY: Decimal("990.00"),
    SubscriptionType.YEARLY: Decimal("1490.00"),
    SubscriptionType.PAY_AS_YOU_GO: Decimal("190.00"),
}

ALLOWED_PAYMENT_METHODS = {"CARD", "CASH"}


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = PaymentRepository(session)

    async def checkout(self, user_id: str, amount: Decimal, method: str) -> Payment:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Direct top-up is disabled. Purchase a subscription instead.",
        )

    def build_subscription_payment(
        self,
        user_id: str,
        subscription_type: SubscriptionType,
        method: str = "CARD",
    ) -> Payment:
        normalized_method = method.upper()
        if normalized_method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment method")

        return Payment(
            user_id=user_id,
            amount=SUBSCRIPTION_PRICES[subscription_type],
            method=normalized_method,
            status="SUCCESS",
            currency="UAH",
        )

    def build_plan_payment(
        self,
        user_id: str,
        plan: MembershipPlan,
        method: str = "CARD",
    ) -> Payment:
        normalized_method = method.upper()
        if normalized_method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment method")

        return Payment(
            user_id=user_id,
            amount=plan.price,
            method=normalized_method,
            status="SUCCESS",
            currency=plan.currency,
        )

    async def list_for_user(self, user_id: str) -> list[Payment]:
        payments = await self.repository.list_by_user(user_id)
        allowed_amounts = set(SUBSCRIPTION_PRICES.values())
        return [payment for payment in payments if payment.amount in allowed_amounts]

    async def list_all(
        self,
        user_id: str | None = None,
        status_filter: str | None = None,
        method: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Payment]:
        if start_date and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)
        return await self.repository.list_all(user_id, status_filter, method, start_date, end_date)

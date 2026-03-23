from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import Response
from starlette.requests import Request

from app.api.routes import auth, bookings, health, payments, public, reports, schedules, subscriptions, users
from app.core.cookies import AuthCookies
from app.models.user import UserRole
from app.schemas.auth import AuthPayload, AuthResult, LoginRequest, RefreshResponse, RegisterRequest
from app.schemas.booking import BookingRead
from app.schemas.payment import PaymentCreateRequest
from app.schemas.report import RevenueReport, TrainerPopularityReport
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.schemas.subscription import SubscriptionFreezeRequest, SubscriptionPurchaseRequest, SubscriptionRead
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserProfileUpdate, UserRead


def make_request(path: str = "/", method: str = "GET") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "cookies": {},
            "state": {},
            "client": ("127.0.0.1", 1234),
        }
    )


def make_user(role: UserRole = UserRole.CLIENT) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="user-1",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        role=role,
        phone="+380501112233",
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


def make_schedule() -> SimpleNamespace:
    start_time = datetime.now(UTC) + timedelta(days=1)
    trainer = make_user(UserRole.TRAINER)
    booking = SimpleNamespace(id="booking-1", user_id="user-1", status="CONFIRMED")
    return SimpleNamespace(
        id="class-1",
        title="Morning Flow",
        description=None,
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=12,
        type="GROUP",
        trainer=trainer,
        bookings=[booking],
        created_at=start_time,
        updated_at=start_time,
    )


def make_booking() -> SimpleNamespace:
    trainer = make_user(UserRole.TRAINER)
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="booking-1",
        user_id="user-1",
        class_id="class-1",
        status="CONFIRMED",
        created_at=now,
        updated_at=now,
        workout_class=SimpleNamespace(
            id="class-1",
            title="Morning Flow",
            trainer_id=trainer.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            capacity=12,
            trainer=trainer,
        ),
    )


def make_attendee() -> SimpleNamespace:
    now = datetime.now(UTC)
    user = make_user()
    return SimpleNamespace(
        id="booking-1",
        user_id=user.id,
        status="CONFIRMED",
        created_at=now,
        user=user,
    )


def make_subscription() -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="subscription-1",
        user_id="user-1",
        type="MONTHLY",
        start_date=now,
        end_date=now + timedelta(days=30),
        status="ACTIVE",
        total_visits=12,
        remaining_visits=11,
        created_at=now,
        updated_at=now,
    )


def make_payment() -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="payment-1",
        user_id="user-1",
        amount=990,
        currency="UAH",
        status="SUCCESS",
        method="CARD",
        user=make_user(),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_auth_routes(monkeypatch):
    captured = {}
    auth_result = AuthResult(
        public_payload=AuthPayload(user=UserRead.model_validate(make_user())),
        cookies=AuthCookies("access", "refresh", "csrf"),
    )

    class FakeAuthService:
        def __init__(self, db):
            self.db = db

        async def register(self, payload, request):
            captured["register"] = (payload, request.url.path)
            return auth_result

        async def login(self, payload, request):
            captured["login"] = (payload, request.url.path)
            return auth_result

        async def refresh(self, request):
            captured["refresh"] = request.url.path
            return auth_result

        async def logout(self, request):
            captured["logout"] = request.url.path

    monkeypatch.setattr(auth, "AuthService", FakeAuthService)
    monkeypatch.setattr(auth, "set_auth_cookies", lambda response, cookies: captured.setdefault("cookies", cookies))
    monkeypatch.setattr(auth, "clear_auth_cookies", lambda response: captured.setdefault("cleared", True))

    request = make_request("/auth/register", "POST")
    response = Response()
    register_payload = RegisterRequest(
        email="new@example.com", password="Password123!", first_name="New", last_name="User"
    )
    register_result = await auth.register(request, register_payload, response, None, object())
    assert register_result.user.email == "user@example.com"
    assert captured["cookies"].access_token == "access"

    login_payload = LoginRequest(email="new@example.com", password="Password123!")
    login_result = await auth.login(make_request("/auth/login", "POST"), login_payload, Response(), None, object())
    assert login_result.user.id == "user-1"

    refresh_result = await auth.refresh(make_request("/auth/refresh", "POST"), Response(), None, object())
    assert isinstance(refresh_result, RefreshResponse)

    logout_result = await auth.logout(make_request("/auth/logout", "POST"), object())
    assert logout_result.status_code == 204
    assert captured["cleared"] is True

    me_result = await auth.me(make_user())
    assert me_result.role == UserRole.CLIENT


@pytest.mark.asyncio
async def test_user_routes(monkeypatch):
    class FakeUserService:
        def __init__(self, db):
            self.db = db

        async def update_profile(self, current_user, payload):
            return current_user

        async def list_users(self, role):
            return [make_user(role or UserRole.CLIENT)]

        async def create_user(self, payload):
            return make_user(payload.role)

        async def update_user(self, user_id, payload):
            user = make_user(payload.role or UserRole.CLIENT)
            user.id = user_id
            return user

    monkeypatch.setattr(users, "UserService", FakeUserService)

    current_user = make_user()
    assert (await users.profile(current_user)).email == current_user.email
    assert (
        await users.update_profile(UserProfileUpdate(first_name="Neo"), current_user, object())
    ).first_name == "Test"
    assert len(await users.list_users(UserRole.TRAINER, make_user(UserRole.ADMIN), object())) == 1

    created = await users.create_user(
        UserAdminCreate(
            email="trainer@example.com",
            password="Password123!",
            first_name="Train",
            last_name="Er",
            role=UserRole.TRAINER,
        ),
        make_user(UserRole.ADMIN),
        object(),
    )
    assert created.role == UserRole.TRAINER

    updated = await users.update_user(
        "user-2",
        UserAdminUpdate(first_name="Updated", role=UserRole.OWNER),
        make_user(UserRole.ADMIN),
        object(),
    )
    assert updated.id == "user-2"


@pytest.mark.asyncio
async def test_schedule_routes(monkeypatch):
    class FakeScheduleService:
        def __init__(self, db):
            self.db = db

        async def create_schedule(self, payload, current_user):
            return make_schedule()

        async def list_schedules(self):
            return [make_schedule()]

        async def list_my_classes(self, user_id):
            return [make_schedule()]

        async def list_attendees(self, class_id, current_user):
            return [make_attendee()]

        async def update_schedule(self, class_id, payload):
            return make_schedule()

        async def delete_schedule(self, class_id):
            return None

    monkeypatch.setattr(schedules, "ScheduleService", FakeScheduleService)
    admin = make_user(UserRole.ADMIN)

    created = await schedules.create_schedule(
        ScheduleCreate(
            title="Morning Flow",
            type="GROUP",
            startTime=datetime.now(UTC) + timedelta(days=1),
            endTime=datetime.now(UTC) + timedelta(days=1, hours=1),
            capacity=12,
            trainerId="trainer-1",
        ),
        admin,
        object(),
    )
    assert isinstance(created, ScheduleRead)
    assert len(await schedules.list_schedules(make_user(), object())) == 1
    assert len(await schedules.my_classes(make_user(UserRole.TRAINER), object())) == 1
    assert len(await schedules.attendees("class-1", make_user(UserRole.TRAINER), object())) == 1
    assert isinstance(await schedules.update_schedule("class-1", ScheduleUpdate(title="Updated"), admin, object()), ScheduleRead)
    assert (await schedules.delete_schedule("class-1", admin, object())).status_code == 204


@pytest.mark.asyncio
async def test_subscription_booking_payment_report_public_and_health_routes(monkeypatch):
    class FakeSubscriptionService:
        def __init__(self, db):
            self.db = db

        async def purchase(self, user_id, subscription_type):
            return make_subscription()

        async def freeze(self, user_id, subscription_id, days):
            return make_subscription()

        async def list_for_user(self, user_id):
            return [make_subscription()]

    class FakeBookingService:
        def __init__(self, db):
            self.db = db

        async def create_booking(self, user_id, class_id):
            return make_booking()

        async def cancel_booking(self, user_id, booking_id):
            return make_booking()

        async def list_for_user(self, user_id):
            return [make_booking()]

    class FakePaymentService:
        def __init__(self, db):
            self.db = db

        async def checkout(self, user_id, amount, method):
            return make_payment()

        async def list_for_user(self, user_id):
            return [make_payment()]

        async def list_all(self, user_id, status_filter, method, start_date, end_date):
            return [make_payment()]

    class FakeReportService:
        def __init__(self, db):
            self.db = db

        async def revenue_report(self, start_date, end_date):
            return RevenueReport(
                period={"startDate": start_date.isoformat(), "endDate": end_date.isoformat()},
                total_revenue=2000,
                transactions_count=3,
                currency="UAH",
            )

        async def trainer_popularity(self):
            return [
                TrainerPopularityReport(
                    trainer_id="trainer-1",
                    name="Coach One",
                    total_attendees=10,
                    classes_taught=4,
                    average_attendees_per_class=2.5,
                )
            ]

    class FakePublicService:
        def __init__(self, db):
            self.db = db

        async def club_stats(self):
            return {"clients_count": 10, "trainers_count": 2, "classes_next_7_days": 4, "active_subscriptions_count": 7}

    class FakeConnection:
        async def execute(self, query):
            return 1

    class FakeBegin:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(subscriptions, "SubscriptionService", FakeSubscriptionService)
    monkeypatch.setattr(bookings, "BookingService", FakeBookingService)
    monkeypatch.setattr(payments, "PaymentService", FakePaymentService)
    monkeypatch.setattr(reports, "ReportService", FakeReportService)
    monkeypatch.setattr(public, "PublicService", FakePublicService)
    async def ping():
        return None

    monkeypatch.setattr(health, "engine", SimpleNamespace(begin=lambda: FakeBegin()))
    monkeypatch.setattr(health, "get_redis", lambda: SimpleNamespace(ping=ping))

    client = make_user(UserRole.CLIENT)
    admin = make_user(UserRole.ADMIN)

    assert isinstance(
        await subscriptions.purchase_subscription(
            SubscriptionPurchaseRequest(type="MONTHLY"), client, None, object()
        ),
        SubscriptionRead,
    )
    assert isinstance(
        await subscriptions.freeze_subscription(
            "subscription-1", SubscriptionFreezeRequest(days=7), client, None, object()
        ),
        SubscriptionRead,
    )
    assert len(await subscriptions.my_subscriptions(client, object())) == 1

    assert isinstance(await bookings.create_booking("class-1", client, object()), BookingRead)
    assert isinstance(await bookings.cancel_booking("booking-1", client, object()), BookingRead)
    assert len(await bookings.my_bookings(client, object())) == 1

    assert (
        await payments.checkout(PaymentCreateRequest(amount=990, method="CARD"), client, object())
    ).amount == 990
    assert len(await payments.my_payments(client, object())) == 1
    assert len(await payments.all_payments(None, None, None, None, None, admin, object())) == 1

    assert (await reports.revenue(None, None, admin, object())).total_revenue == 2000
    assert len(await reports.trainer_popularity(admin, object())) == 1
    assert (await public.club_stats(object()))["clients_count"] == 10
    assert await health.live() == {"status": "ok"}
    assert await health.ready() == {"status": "ready"}

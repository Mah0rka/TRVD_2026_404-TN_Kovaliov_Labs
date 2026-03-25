# Коротко: тести перевіряють сценарії модуля runtime scripts.

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.scripts import bootstrap_db, seed_demo
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.tasks import celery_app


def test_run_alembic_command(monkeypatch):
    monkeypatch.setattr(bootstrap_db.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    bootstrap_db._run_alembic_command("upgrade", "head")

    monkeypatch.setattr(bootstrap_db.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=3))
    with pytest.raises(SystemExit):
        bootstrap_db._run_alembic_command("upgrade", "head")


@pytest.mark.asyncio
async def test_ensure_migrations_applied(monkeypatch):
    commands = []

    class FakeConnection:
        def __init__(self, table_names):
            self.table_names = table_names

        async def run_sync(self, fn):
            return self.table_names

    class FakeBegin:
        def __init__(self, table_names):
            self.table_names = table_names

        async def __aenter__(self):
            return FakeConnection(self.table_names)

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(bootstrap_db, "_run_alembic_command", lambda *args: commands.append(args))
    monkeypatch.setattr(bootstrap_db, "engine", SimpleNamespace(begin=lambda: FakeBegin(["users"])))
    await bootstrap_db.ensure_migrations_applied()
    assert commands[-1] == ("stamp", "head")

    monkeypatch.setattr(bootstrap_db, "engine", SimpleNamespace(begin=lambda: FakeBegin(["alembic_version"])))
    await bootstrap_db.ensure_migrations_applied()
    assert commands[-1] == ("upgrade", "head")


def test_script_main_wrappers(monkeypatch):
    called = []

    def fake_run(coro):
        called.append(coro.cr_code.co_name)
        coro.close()
        return "done"

    monkeypatch.setattr(bootstrap_db.asyncio, "run", fake_run)
    monkeypatch.setattr(seed_demo.asyncio, "run", fake_run)
    monkeypatch.setattr(celery_app.asyncio, "run", fake_run)

    bootstrap_db.main()
    seed_demo.main()
    assert "ensure_migrations_applied" in called
    assert "seed_demo_data" in called
    assert celery_app.expire_subscriptions() == "done"
    assert celery_app.subscription_reminders() == "done"
    assert celery_app.ping() == "pong"


@pytest.mark.asyncio
async def test_seed_helpers(monkeypatch):
    monkeypatch.setattr(seed_demo, "hash_password", lambda value: "hashed")

    class FakeScalarResult:
        def __init__(self, item=None):
            self.item = item

        def scalar_one_or_none(self):
            return self.item

        def first(self):
            return self.item

    class FakeExecuteResult:
        def __init__(self, item=None):
            self.item = item

        def scalar_one_or_none(self):
            return self.item

        def scalars(self):
            return FakeScalarResult(self.item)

    class FakeSession:
        def __init__(self):
            self.added = []
            self.added_all = []

        async def execute(self, statement):
            return FakeExecuteResult(None)

        def add(self, item):
            self.added.append(item)

        def add_all(self, items):
            self.added_all.extend(items)

        async def flush(self):
            return None

    session = FakeSession()
    users_map = await seed_demo._ensure_users(session)
    assert set(users_map.keys()) == {"owner", "admin", "trainer", "client"}
    plans_map = await seed_demo._ensure_membership_plans(session)
    assert set(plans_map.keys()) == {"monthly", "yearly", "dropin", "private_comp"}

    await seed_demo._ensure_schedule(session, users_map["trainer"])
    assert len(session.added_all) == 2

    await seed_demo._ensure_subscription(session, users_map["client"], plans_map["monthly"])
    await seed_demo._ensure_payment(session, users_map["client"], plans_map["monthly"])
    assert len(session.added) >= 9


@pytest.mark.asyncio
async def test_reconcile_legacy_demo_users_moves_relations_and_deletes_legacy():
    now = datetime.now(UTC)
    canonical_client = SimpleNamespace(id="client-new", email="client@example.com")
    canonical_trainer = SimpleNamespace(id="trainer-new", email="trainer@example.com")
    canonical_owner = SimpleNamespace(id="owner-new", email="owner@example.com")
    canonical_admin = SimpleNamespace(id="admin-new", email="admin@example.com")

    legacy_client = SimpleNamespace(id="client-old", email="client@fcms.local")
    legacy_trainer = SimpleNamespace(id="trainer-old", email="trainer@fcms.local")

    subscription = Subscription(
        user_id="client-old",
        type=SubscriptionType.MONTHLY,
        start_date=now,
        end_date=now + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=12,
    )
    payment = Payment(user_id="client-old", amount=100, currency="UAH", status="SUCCESS", method="CARD")
    booking = Booking(user_id="client-old", class_id="class-1", status="CONFIRMED")
    workout_class = SimpleNamespace(trainer_id="trainer-old")

    class FakeScalarResult:
        def __init__(self, items):
            self.items = items

        def all(self):
            return self.items

    class FakeExecuteResult:
        def __init__(self, one=None, many=None):
            self.one = one
            self.many = many or []

        def scalar_one_or_none(self):
            return self.one

        def scalars(self):
            return FakeScalarResult(self.many)

    class FakeSession:
        def __init__(self):
            self.deleted = []

        async def execute(self, statement):
            compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
            if "users.email = 'client@fcms.local'" in compiled:
                return FakeExecuteResult(one=legacy_client)
            if "users.email = 'trainer@fcms.local'" in compiled:
                return FakeExecuteResult(one=legacy_trainer)
            if "users.email = 'owner@fcms.local'" in compiled or "users.email = 'admin@fcms.local'" in compiled:
                return FakeExecuteResult(one=None)
            if "FROM subscriptions" in compiled and "user_id = 'client-old'" in compiled:
                return FakeExecuteResult(many=[subscription])
            if "FROM payments" in compiled and "user_id = 'client-old'" in compiled:
                return FakeExecuteResult(many=[payment])
            if "FROM bookings" in compiled and "user_id = 'client-old'" in compiled:
                return FakeExecuteResult(many=[booking])
            if "FROM workout_classes" in compiled and "trainer_id = 'trainer-old'" in compiled:
                return FakeExecuteResult(many=[workout_class])
            return FakeExecuteResult(one=None, many=[])

        async def delete(self, item):
            self.deleted.append(item.email)

        async def flush(self):
            return None

    session = FakeSession()
    await seed_demo._reconcile_legacy_demo_users(
        session,
        {
            "owner": canonical_owner,
            "admin": canonical_admin,
            "trainer": canonical_trainer,
            "client": canonical_client,
        },
    )

    assert subscription.user_id == "client-new"
    assert payment.user_id == "client-new"
    assert booking.user_id == "client-new"
    assert workout_class.trainer_id == "trainer-new"
    assert session.deleted == ["trainer@fcms.local", "client@fcms.local"]

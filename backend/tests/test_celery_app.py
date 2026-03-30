# Тести перевіряють точки входу celery-задач.

import inspect
from types import SimpleNamespace

import pytest

from app.tasks import celery_app


class FakeSessionContext:
    # Імітує async context manager для async_session_factory у тестах.
    def __init__(self, session) -> None:
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


# Перевіряє, що ping повертає службову відповідь worker-перевірки.
def test_ping_returns_pong():
    assert celery_app.ping() == "pong"


# Перевіряє, що expire-subscriptions coroutine використовує NotificationService.
@pytest.mark.asyncio
async def test_run_expire_subscriptions_uses_notification_service(monkeypatch):
    fake_session = object()

    class FakeNotificationService:
        def __init__(self, session) -> None:
            assert session is fake_session

        async def expire_subscriptions(self) -> int:
            return 2

    async def fake_run_with_isolated_session(operation):
        return await operation(fake_session)

    monkeypatch.setattr(celery_app, "_run_with_isolated_session", fake_run_with_isolated_session)
    monkeypatch.setattr(celery_app, "NotificationService", FakeNotificationService)

    assert await celery_app._run_expire_subscriptions() == 2


# Перевіряє, що reminders coroutine використовує NotificationService.
@pytest.mark.asyncio
async def test_run_subscription_reminders_uses_notification_service(monkeypatch):
    fake_session = object()
    reminder_payload = [{"subscription_id": "sub-1"}]

    class FakeNotificationService:
        def __init__(self, session) -> None:
            assert session is fake_session

        async def collect_expiration_reminders(self):
            return reminder_payload

    async def fake_run_with_isolated_session(operation):
        return await operation(fake_session)

    monkeypatch.setattr(celery_app, "_run_with_isolated_session", fake_run_with_isolated_session)
    monkeypatch.setattr(celery_app, "NotificationService", FakeNotificationService)

    assert await celery_app._run_subscription_reminders() == reminder_payload


# Перевіряє, що materialization coroutine використовує ScheduleService.
@pytest.mark.asyncio
async def test_run_materialize_future_occurrences_uses_schedule_service(monkeypatch):
    fake_session = object()

    class FakeScheduleService:
        def __init__(self, session) -> None:
            assert session is fake_session

        async def materialize_future_occurrences(self) -> int:
            return 5

    async def fake_run_with_isolated_session(operation):
        return await operation(fake_session)

    monkeypatch.setattr(celery_app, "_run_with_isolated_session", fake_run_with_isolated_session)
    monkeypatch.setattr(celery_app, "ScheduleService", FakeScheduleService)

    assert await celery_app._run_materialize_future_occurrences() == 5


# Перевіряє, що isolated session helper закриває engine після виконання операції.
@pytest.mark.asyncio
async def test_run_with_isolated_session_disposes_engine(monkeypatch):
    fake_session = object()

    class FakeEngine:
        def __init__(self) -> None:
            self.disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    fake_engine = FakeEngine()
    monkeypatch.setattr(
        celery_app,
        "_create_task_session_factory",
        lambda: (fake_engine, lambda: FakeSessionContext(fake_session)),
    )

    async def operation(session):
        assert session is fake_session
        return "ok"

    assert await celery_app._run_with_isolated_session(operation) == "ok"
    assert fake_engine.disposed is True


# Перевіряє, що sync-wrapper-и делегують виконання через asyncio.run.
def test_celery_wrappers_delegate_to_asyncio_run(monkeypatch):
    captured = []

    def fake_run(coroutine):
        captured.append(coroutine.cr_code.co_name if inspect.iscoroutine(coroutine) else None)
        if inspect.iscoroutine(coroutine):
            coroutine.close()
        return len(captured)

    monkeypatch.setattr(celery_app.asyncio, "run", fake_run)

    assert celery_app.expire_subscriptions() == 1
    assert celery_app.subscription_reminders() == 2
    assert celery_app.materialize_future_occurrences() == 3
    assert captured == [
        "_run_expire_subscriptions",
        "_run_subscription_reminders",
        "_run_materialize_future_occurrences",
    ]

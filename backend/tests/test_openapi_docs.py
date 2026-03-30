# Тести перевіряють, що OpenAPI-специфікація містить описи та приклади.

from app.main import app


def test_openapi_includes_descriptions_and_examples():
    schema = app.openapi()

    assert schema["info"]["summary"]
    assert schema["info"]["description"]

    register_operation = schema["paths"]["/auth/register"]["post"]
    assert register_operation["summary"] == "Зареєструвати нового користувача"
    assert "сесію" in register_operation["description"].lower()
    assert register_operation["responses"]["201"]["content"]["application/json"]["example"]["user"]["email"] == (
        "anna.koval@example.com"
    )

    schedules_create = schema["paths"]["/schedules"]["post"]
    assert schedules_create["responses"]["201"]["content"]["application/json"]["example"]["id"] == (
        "class-2026-04-01-0800"
    )
    assert schedules_create["responses"]["400"]["content"]["application/json"]["example"]["detail"]

    freeze_operation = schema["paths"]["/subscriptions/{subscription_id}/freeze"]["patch"]
    assert freeze_operation["responses"]["429"]["content"]["application/json"]["example"]["code"] == "http_error"

    register_schema = schema["components"]["schemas"]["RegisterRequest"]
    assert register_schema["example"]["email"] == "anna.koval@example.com"

    schedule_schema = schema["components"]["schemas"]["ScheduleCreate"]
    assert schedule_schema["example"]["recurrence"]["byWeekday"] == ["MO", "WE", "FR"]

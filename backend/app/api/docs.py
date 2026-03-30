# Модуль централізує OpenAPI-описи, приклади та типові відповіді Swagger.

from typing import Any

REQUEST_ID_EXAMPLE = "req_01HV7JQ4KQ6P1H9R5V2M8C7D3F"

API_SUMMARY = "API для керування фітнес-клубом: користувачі, розклад, бронювання, платежі та абонементи."

API_DESCRIPTION = """
MotionLab API покриває типові сценарії роботи фітнес-клубу:
авторизацію через cookie-сесію, керування користувачами, розкладом,
бронюваннями, абонементами, платежами та адміністративною звітністю.

У Swagger нижче:
- для запитів наведені реалістичні приклади payload-ів;
- для ключових маршрутів описані очікувані бізнес-сценарії;
- для типових помилок показано фактичний формат відповіді API.
""".strip()

OPENAPI_TAGS = [
    {"name": "health", "description": "Перевірка доступності сервісу та готовності інфраструктури."},
    {"name": "public", "description": "Публічні дані для лендингу та каталогу абонементів."},
    {"name": "auth", "description": "Реєстрація, вхід, оновлення сесії та профіль поточного користувача."},
    {"name": "bookings", "description": "Запис клієнта на заняття та керування власними бронюваннями."},
    {"name": "payments", "description": "Історія платежів клієнтів і адміністративний реєстр транзакцій."},
    {"name": "reports", "description": "Звіти по доходах і популярності тренерів для менеджменту."},
    {"name": "schedules", "description": "Створення, перегляд і зміна розкладу занять, зокрема recurring-серій."},
    {"name": "subscriptions", "description": "Плани абонементів, покупки клієнтів і management-операції."},
    {"name": "users", "description": "Профіль поточного користувача та адміністрування користувачів."},
]

USER_EXAMPLE = {
    "id": "user-7f6c4d4c",
    "email": "anna.koval@example.com",
    "first_name": "Анна",
    "last_name": "Коваль",
    "role": "CLIENT",
    "phone": "+380501112233",
    "is_verified": True,
    "created_at": "2026-03-15T09:30:00Z",
    "updated_at": "2026-03-27T14:10:00Z",
}

TRAINER_EXAMPLE = {
    "id": "trainer-1d4a9f5b",
    "first_name": "Олег",
    "last_name": "Мельник",
}

REGISTER_REQUEST_EXAMPLE = {
    "email": "anna.koval@example.com",
    "password": "StrongPass123!",
    "first_name": "Анна",
    "last_name": "Коваль",
}

LOGIN_REQUEST_EXAMPLE = {
    "email": "anna.koval@example.com",
    "password": "StrongPass123!",
}

AUTH_PAYLOAD_EXAMPLE = {"user": USER_EXAMPLE}
REFRESH_RESPONSE_EXAMPLE = {"user": USER_EXAMPLE}

USER_PROFILE_UPDATE_EXAMPLE = {
    "first_name": "Анна-Марія",
    "last_name": "Коваль",
    "phone": "+380501112244",
}

USER_ADMIN_CREATE_EXAMPLE = {
    "email": "coach.ivanenko@example.com",
    "password": "StrongPass123!",
    "first_name": "Іван",
    "last_name": "Іваненко",
    "phone": "+380671234567",
    "role": "TRAINER",
    "is_verified": True,
}

USER_ADMIN_UPDATE_EXAMPLE = {
    "first_name": "Іван",
    "last_name": "Іваненко",
    "phone": "+380671234568",
    "role": "ADMIN",
    "is_verified": True,
}

MEMBERSHIP_PLAN_EXAMPLE = {
    "id": "plan-monthly-12",
    "title": "Місячний 12 занять",
    "description": "12 відвідувань групових занять протягом 30 днів.",
    "type": "MONTHLY",
    "duration_days": 30,
    "visits_limit": 12,
    "price": 990.0,
    "currency": "UAH",
    "sort_order": 10,
    "is_active": True,
    "is_public": True,
    "created_at": "2026-03-01T08:00:00Z",
    "updated_at": "2026-03-20T10:15:00Z",
}

MEMBERSHIP_PLAN_CREATE_EXAMPLE = {
    "title": "Річний безліміт",
    "description": "365 днів доступу до клубу та групових занять.",
    "type": "YEARLY",
    "duration_days": 365,
    "visits_limit": None,
    "price": 14990.0,
    "currency": "UAH",
    "sort_order": 20,
    "is_active": True,
    "is_public": True,
}

MEMBERSHIP_PLAN_UPDATE_EXAMPLE = {
    "title": "Місячний 16 занять",
    "description": "Оновлений тариф для активних клієнтів.",
    "price": 1190.0,
    "visits_limit": 16,
    "sort_order": 15,
}

CLUB_STATS_EXAMPLE = {
    "clients_count": 238,
    "trainers_count": 12,
    "classes_next_7_days": 46,
    "active_subscriptions_count": 181,
}

SCHEDULE_RECURRENCE_EXAMPLE = {
    "frequency": "WEEKLY",
    "interval": 1,
    "byWeekday": ["MO", "WE", "FR"],
    "count": 12,
    "until": None,
}

SCHEDULE_RECURRENCE_READ_EXAMPLE = {
    **SCHEDULE_RECURRENCE_EXAMPLE,
    "summary": "Щопонеділка, щосереди та щопʼятниці, 12 повторів",
}

SCHEDULE_CREATE_EXAMPLE = {
    "title": "Morning Flow",
    "type": "GROUP",
    "startTime": "2026-04-01T08:00:00Z",
    "endTime": "2026-04-01T09:00:00Z",
    "capacity": 16,
    "trainerId": "trainer-1d4a9f5b",
    "isPaidExtra": False,
    "extraPrice": None,
    "recurrence": SCHEDULE_RECURRENCE_EXAMPLE,
}

SCHEDULE_UPDATE_EXAMPLE = {
    "title": "Morning Flow Advanced",
    "startTime": "2026-04-03T08:30:00Z",
    "endTime": "2026-04-03T09:30:00Z",
    "capacity": 18,
    "scope": "FOLLOWING",
}

SCHEDULE_COMPLETE_EXAMPLE = {
    "comment": "Заняття проведено повністю, присутні 11 клієнтів.",
}

BOOKING_SUMMARY_EXAMPLE = {
    "id": "booking-3021",
    "user_id": "user-7f6c4d4c",
    "status": "CONFIRMED",
}

SCHEDULE_EXAMPLE = {
    "id": "class-2026-04-01-0800",
    "title": "Morning Flow",
    "description": None,
    "trainer_id": "trainer-1d4a9f5b",
    "start_time": "2026-04-01T08:00:00Z",
    "end_time": "2026-04-01T09:00:00Z",
    "capacity": 16,
    "type": "GROUP",
    "is_paid_extra": False,
    "extra_price": None,
    "series_id": "series-morning-flow",
    "source_occurrence_start": "2026-04-01T08:00:00Z",
    "is_series_exception": False,
    "recurrence": SCHEDULE_RECURRENCE_READ_EXAMPLE,
    "trainer": TRAINER_EXAMPLE,
    "completed_at": None,
    "completion_comment": None,
    "completed_by": None,
    "bookings": [BOOKING_SUMMARY_EXAMPLE],
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-20T10:00:00Z",
}

ATTENDEE_USER_EXAMPLE = {
    "id": "user-7f6c4d4c",
    "email": "anna.koval@example.com",
    "first_name": "Анна",
    "last_name": "Коваль",
}

SCHEDULE_ATTENDEE_EXAMPLE = {
    "id": "booking-3021",
    "user_id": "user-7f6c4d4c",
    "status": "CONFIRMED",
    "created_at": "2026-03-30T17:12:00Z",
    "user": ATTENDEE_USER_EXAMPLE,
}

BOOKING_CLASS_SUMMARY_EXAMPLE = {
    "id": "class-2026-04-01-0800",
    "title": "Morning Flow",
    "trainer_id": "trainer-1d4a9f5b",
    "start_time": "2026-04-01T08:00:00Z",
    "end_time": "2026-04-01T09:00:00Z",
    "capacity": 16,
    "is_paid_extra": False,
    "extra_price": None,
    "trainer": TRAINER_EXAMPLE,
}

BOOKING_EXAMPLE = {
    "id": "booking-3021",
    "user_id": "user-7f6c4d4c",
    "class_id": "class-2026-04-01-0800",
    "status": "CONFIRMED",
    "created_at": "2026-03-30T17:12:00Z",
    "updated_at": "2026-03-30T17:12:00Z",
    "workout_class": BOOKING_CLASS_SUMMARY_EXAMPLE,
}

PAYMENT_CREATE_EXAMPLE = {
    "amount": 990.0,
    "method": "CARD",
}

PAYMENT_EXAMPLE = {
    "id": "payment-9001",
    "user_id": "user-7f6c4d4c",
    "amount": 990.0,
    "currency": "UAH",
    "status": "SUCCESS",
    "method": "CARD",
    "purpose": "SUBSCRIPTION",
    "description": "Покупка абонемента: Місячний 12 занять",
    "booking_class_id": None,
    "user": USER_EXAMPLE,
    "created_at": "2026-03-28T12:15:00Z",
    "updated_at": "2026-03-28T12:15:00Z",
}

SUBSCRIPTION_PURCHASE_EXAMPLE = {
    "plan_id": "plan-monthly-12",
    "type": None,
}

SUBSCRIPTION_FREEZE_EXAMPLE = {"days": 14}

SUBSCRIPTION_MANAGEMENT_UPDATE_EXAMPLE = {
    "status": "FROZEN",
    "end_date": "2026-05-15T23:59:59Z",
    "remaining_visits": 10,
}

SUBSCRIPTION_ISSUE_EXAMPLE = {
    "user_id": "user-7f6c4d4c",
    "plan_id": "plan-monthly-12",
    "start_date": "2026-04-01T00:00:00Z",
    "end_date": "2026-05-01T00:00:00Z",
    "status": "ACTIVE",
    "total_visits": 12,
    "remaining_visits": 12,
}

SUBSCRIPTION_EXAMPLE = {
    "id": "subscription-501",
    "user_id": "user-7f6c4d4c",
    "plan_id": "plan-monthly-12",
    "type": "MONTHLY",
    "start_date": "2026-04-01T00:00:00Z",
    "end_date": "2026-05-01T00:00:00Z",
    "status": "ACTIVE",
    "total_visits": 12,
    "remaining_visits": 11,
    "user": USER_EXAMPLE,
    "plan": MEMBERSHIP_PLAN_EXAMPLE,
    "last_modified_by": USER_EXAMPLE,
    "last_modified_at": "2026-03-28T12:15:00Z",
    "deleted_by": None,
    "deleted_at": None,
    "restored_by": None,
    "restored_at": None,
    "created_at": "2026-03-28T12:15:00Z",
    "updated_at": "2026-03-28T12:15:00Z",
}

REVENUE_REPORT_EXAMPLE = {
    "period": {
        "startDate": "2026-03-01T00:00:00Z",
        "endDate": "2026-03-31T23:59:59Z",
    },
    "total_revenue": 64250.0,
    "transactions_count": 87,
    "currency": "UAH",
}

TRAINER_POPULARITY_EXAMPLE = {
    "trainer_id": "trainer-1d4a9f5b",
    "name": "Олег Мельник",
    "total_attendees": 94,
    "classes_taught": 18,
    "average_attendees_per_class": 5.22,
}

HEALTH_LIVE_EXAMPLE = {"status": "ok"}
HEALTH_READY_EXAMPLE = {"status": "ready"}


def response_example(description: str, example: Any) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "example": example,
            }
        },
    }


def error_body(detail: str) -> dict[str, Any]:
    return {
        "detail": detail,
        "code": "http_error",
        "request_id": REQUEST_ID_EXAMPLE,
    }


VALIDATION_ERROR_BODY = {
    "detail": "Validation failed",
    "code": "validation_error",
    "request_id": REQUEST_ID_EXAMPLE,
    "errors": [
        {
            "type": "string_too_short",
            "loc": ["body", "password"],
            "msg": "String should have at least 8 characters",
            "input": "12345",
            "ctx": {"min_length": 8},
        }
    ],
}


VALIDATION_ERROR_RESPONSE = {
    422: response_example("Помилка валідації параметрів або тіла запиту.", VALIDATION_ERROR_BODY)
}

AUTH_REQUIRED_RESPONSE = {
    401: response_example(
        "Користувач неавторизований або сесія недійсна.",
        error_body("Authentication required"),
    )
}

PERMISSION_DENIED_RESPONSE = {
    403: response_example(
        "Користувач не має достатніх прав для виконання операції.",
        error_body("Insufficient permissions"),
    )
}

RATE_LIMIT_RESPONSE = {
    429: response_example(
        "Перевищено дозволену частоту звернень до endpoint-а.",
        error_body("Too many requests. Please try again later."),
    )
}


def bad_request_response(description: str, detail: str) -> dict[int, dict[str, Any]]:
    return {400: response_example(description, error_body(detail))}


def not_found_response(description: str, detail: str) -> dict[int, dict[str, Any]]:
    return {404: response_example(description, error_body(detail))}


def conflict_response(description: str, detail: str) -> dict[int, dict[str, Any]]:
    return {409: response_example(description, error_body(detail))}


def gone_response(description: str, detail: str) -> dict[int, dict[str, Any]]:
    return {410: response_example(description, error_body(detail))}


def no_content_response(description: str) -> dict[str, Any]:
    return {"description": description}


def merge_responses(*groups: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    for group in groups:
        merged.update(group)
    return merged

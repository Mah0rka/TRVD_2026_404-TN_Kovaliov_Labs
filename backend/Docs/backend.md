# Backend Documentation

## Огляд

`backend` реалізований як modular monolith на `FastAPI` з розділенням на шари
`routes -> services -> repositories -> models/schemas`.
API відповідає за безпечну cookie-based автентифікацію, роботу з користувачами,
розкладом, бронюваннями, абонементами, платежами, звітами, підтвердженням
завершених занять та фоновими задачами.

## Технологічний стек

| Категорія | Технології |
|---|---|
| Web API | FastAPI, Pydantic v2 |
| Дані | SQLAlchemy 2.0 Async ORM, PostgreSQL, Alembic |
| Безпека | JWT, Argon2, HttpOnly cookies, CSRF, RBAC |
| Стан сесій | Redis |
| Фонові задачі | Celery, Celery Beat |
| Тести | pytest, pytest-asyncio, httpx |

## Архітектура модулів

| Папка | Призначення |
|---|---|
| `app/api` | HTTP-маршрути, залежності FastAPI, статус-коди |
| `app/services` | бізнес-логіка та оркестрація сценаріїв |
| `app/repositories` | доступ до БД через SQLAlchemy |
| `app/models` | ORM-моделі домену |
| `app/schemas` | DTO, валідація та контракти API |
| `app/core` | конфігурація, безпека, Redis, логування |
| `app/middleware` | CSRF і request context |
| `app/tasks` | Celery worker та beat-задачі |
| `app/scripts` | bootstrap міграцій і seed-даних |
| `tests` | інтеграційні та unit-тести |

## Доменна модель

| Сутність | Ключові поля | Зв'язки |
|---|---|---|
| `User` | `email`, `password_hash`, `role`, `is_verified` | має багато `Subscription`, `Booking`, `Payment`, `WorkoutClass` |
| `MembershipPlan` | `title`, `type`, `duration_days`, `visits_limit`, `price` | має багато `Subscription` |
| `Subscription` | `plan_id`, `type`, `start_date`, `end_date`, `status`, `remaining_visits` | належить `User` і `MembershipPlan` |
| `WorkoutClass` | `title`, `trainer_id`, `start_time`, `end_time`, `capacity`, `type`, `extra_price`, `series_id`, `source_occurrence_start`, `is_series_exception`, `completed_at`, `completion_comment` | належить тренеру `User`, може належати recurring-серії `WorkoutSeries`, має багато `Booking`, містить службове підтвердження завершення |
| `WorkoutSeries` | `trainer_id`, `start_time`, `end_time`, `frequency`, `interval`, `by_weekday`, `count`, `until`, `rule_text` | належить тренеру `User`, materialize-ить багато `WorkoutClass`, має винятки `WorkoutSeriesExclusion` |
| `Booking` | `user_id`, `class_id`, `status` | зв'язує `User` і `WorkoutClass` |
| `Payment` | `amount`, `status`, `method`, `purpose`, `booking_class_id`, `description` | належить `User` |

## Основні API-модулі

| Префікс | Призначення | Ролі |
|---|---|---|
| `/auth` | register, login, refresh, logout, me | public + authenticated |
| `/users` | профіль, керування користувачами | authenticated / admin / owner |
| `/schedules` | CRUD занять, recurring-серії, список класів, класи тренера, учасники, підтвердження завершення | all roles / trainer / admin / owner |
| `/bookings` | бронювання, checkout extra-занять, скасування | client |
| `/subscriptions` | плани, покупка, freeze, management CRUD | client / admin / owner |
| `/payments` | checkout, історія оплат, управлінський реєстр | client / admin / owner |
| `/reports` | revenue report, trainer popularity | admin / owner |
| `/public` | клубна статистика, публічні плани | public |
| `/health` | live/ready probes | public |

## Автентифікація та безпека

1. `register` створює першого користувача як `OWNER`, а всіх наступних як `CLIENT`, з хешем пароля `Argon2`.
2. `login` видає `access` і `refresh` JWT у `HttpOnly` cookies.
3. `refresh` ротуює refresh session і перевидає пару токенів.
4. Redis зберігає активні сесії та idle-timeout для `ADMIN`/`OWNER`.
5. `CSRFMiddleware` перевіряє `X-CSRF-Token` для mutating-запитів.
6. `require_roles(...)` обмежує доступ до керівних маршрутів.
7. Redis rate limiting застосовується до `login`, `register`, `refresh` і критичних дій.

## Фонові задачі

- `celery worker` виконує асинхронні задачі клубу.
- `celery beat` запускає періодичні перевірки.
- Поточний фокус: нагадування про завершення абонементів, expire-flow і materialization recurring-серій.

## Recurring Schedule Flow

1. `ScheduleCreate.recurrence` дозволяє створити recurring-серію замість одиночного заняття.
2. У `WorkoutSeries` зберігається шаблон правила (`frequency`, `interval`, `by_weekday`, `count` / `until`, `rule_text`).
3. Окремі `WorkoutClass`-occurrence materialize-яться в межах горизонту `schedule_materialization_horizon_days`.
4. `scope=OCCURRENCE | FOLLOWING | SERIES` визначає, чи зміна стосується одного заняття, всіх наступних або всієї серії.
5. Для видалених окремих occurrences зберігаються `WorkoutSeriesExclusion`, щоб materialization не відновлював їх повторно.

## Ключові бізнес-правила

1. `WorkoutClass.end_time` завжди має бути пізніше за `start_time`.
2. Платне додаткове заняття обов'язково містить `extra_price`, інакше створення або оновлення блокується.
3. Клієнтські активні списки приховують заняття, які вже завершилися за `end_time`.
4. Підтвердити завершення заняття можна лише після фактичного `end_time`.
5. Підтвердження завершення доступне тренеру свого заняття або менеджменту (`ADMIN` / `OWNER`).
6. Після підтвердження у `WorkoutClass` зберігаються `completed_at`, `completed_by_id` і `completion_comment`.
7. Будь-яке заняття, включно з recurring-occurrence, дозволено лише в межах локального часу клубу `06:00-22:00`.
8. Weekly-recurring правило повинно містити хоча б один день тижня; одночасне використання `count` і `until` заборонене.
9. Серію не можна змінювати або видаляти, якщо в зачеплених occurrences уже є підтверджені бронювання.

## Запуск

### Docker

```bash
docker compose up --build backend backend-worker backend-beat postgres redis
```

### Продакшн без Nginx

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up --build -d
```

- `Dockerfile.prod` збирає фронтенд і копіює `dist` у продовий образ.
- `FastAPI` віддає SPA зі змінної `FRONTEND_DIST_PATH`, тому окремий `Nginx` не потрібен.
- перший акаунт у порожній базі автоматично отримує роль `OWNER`.

### Локально без Docker

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install poetry
poetry install
python -m app.scripts.bootstrap_db
python -m app.scripts.seed_demo
uvicorn app.main:app --reload
```

## Тестування

```powershell
./scripts/test-backend.ps1
```

Актуальний стан перевірки на 2026-03-28:

- `101/101` backend-тестів проходять успішно.
- загальне тестове покриття бекенду: `90%`.
- покриття recurring-модулів (`schedule_service`, `schedule_recurrence`, `workout_series_repository`, `schedule_repository`, `celery_app`, `schedule schemas`) становить `100%`.

## Корисні точки входу

- `backend/app/main.py` - створення FastAPI застосунку.
- `backend/app/api/router.py` - підключення всіх маршрутів.
- `backend/app/services/auth_service.py` - auth flow і rotation refresh-токенів.
- `backend/app/services/subscription_service.py` - покупки, freeze, management flow.
- `backend/app/services/booking_service.py` - правила бронювання та скасування.
- `backend/app/services/schedule_service.py` - CRUD занять, recurring-серії, список класів, підтвердження завершення.
- `backend/app/services/schedule_recurrence.py` - RRULE helper-и, summary і materialization helpers.

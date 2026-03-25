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
| `WorkoutClass` | `title`, `trainer_id`, `start_time`, `end_time`, `capacity`, `type`, `extra_price`, `completed_at`, `completion_comment` | належить тренеру `User`, має багато `Booking`, містить службове підтвердження завершення |
| `Booking` | `user_id`, `class_id`, `status` | зв'язує `User` і `WorkoutClass` |
| `Payment` | `amount`, `status`, `method`, `purpose`, `booking_class_id`, `description` | належить `User` |

## Основні API-модулі

| Префікс | Призначення | Ролі |
|---|---|---|
| `/auth` | register, login, refresh, logout, me | public + authenticated |
| `/users` | профіль, керування користувачами | authenticated / admin / owner |
| `/schedules` | CRUD занять, список класів, класи тренера, учасники, підтвердження завершення | all roles / trainer / admin / owner |
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
- Поточний фокус: нагадування про завершення абонементів і службові maintenance-сценарії.

## Ключові бізнес-правила

1. `WorkoutClass.end_time` завжди має бути пізніше за `start_time`.
2. Платне додаткове заняття обов'язково містить `extra_price`, інакше створення або оновлення блокується.
3. Клієнтські активні списки приховують заняття, які вже завершилися за `end_time`.
4. Підтвердити завершення заняття можна лише після фактичного `end_time`.
5. Підтвердження завершення доступне тренеру свого заняття або менеджменту (`ADMIN` / `OWNER`).
6. Після підтвердження у `WorkoutClass` зберігаються `completed_at`, `completed_by_id` і `completion_comment`.

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

Актуальний стан перевірки на 2026-03-25:

- `56/56` backend-тестів проходять успішно.
- тестове покриття бекенду: `86%`.

## Корисні точки входу

- `backend/app/main.py` - створення FastAPI застосунку.
- `backend/app/api/router.py` - підключення всіх маршрутів.
- `backend/app/services/auth_service.py` - auth flow і rotation refresh-токенів.
- `backend/app/services/subscription_service.py` - покупки, freeze, management flow.
- `backend/app/services/booking_service.py` - правила бронювання та скасування.
- `backend/app/services/schedule_service.py` - CRUD занять, список класів, підтвердження завершення.

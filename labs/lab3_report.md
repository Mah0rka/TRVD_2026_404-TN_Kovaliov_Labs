# Лабораторна робота №3

## Тема

Розробка серверної частини (Back-end) та API для **Fitness Club Management System**.

## Мета роботи

Реалізувати шар доступу до даних, сервісний шар і REST API, який надає зовнішній
контракт для взаємодії з клієнтською частиною та адміністративним інтерфейсом.

## Архітектурна реалізація

### Data Access Layer

- Для роботи з БД використано `SQLAlchemy 2.0 Async ORM`.
- Сутності описані окремими ORM-моделями: `User`, `MembershipPlan`, `Subscription`,
  `WorkoutClass`, `Booking`, `Payment`.
- Доступ до даних ізольований у репозиторіях, наприклад:
  `UserRepository`, `SubscriptionRepository`, `PaymentRepository`, `ScheduleRepository`.

### Service Layer

- `AuthService` керує register/login/refresh/logout.
- `ScheduleService` відповідає за CRUD розкладу.
- `BookingService` перевіряє `capacity`, дублікати та правила скасування.
- `SubscriptionService` обробляє покупку, freeze та management-сценарії.
- `ReportService` формує фінансові та операційні звіти.

### Dependency Injection

FastAPI `Depends(...)` використовується для:

- видачі `AsyncSession`;
- отримання поточного користувача;
- role-based перевірок;
- rate limit policy на критичних маршрутах.

## Обраний API-стандарт

У проєкті реалізовано **RESTful API** з автоматичною документацією Swagger/OpenAPI.

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Основні REST-маршрути

| Модуль | Основні методи |
|---|---|
| `/auth` | `POST /register`, `POST /login`, `POST /refresh`, `POST /logout`, `GET /me` |
| `/users` | `GET /profile`, `PATCH /profile`, `GET /`, `POST /`, `PATCH /{user_id}`, `DELETE /{user_id}` |
| `/schedules` | `POST /`, `GET /`, `GET /my-classes`, `GET /{class_id}/attendees`, `PATCH /{class_id}`, `DELETE /{class_id}` |
| `/bookings` | `POST /{class_id}`, `POST /{class_id}/checkout`, `POST /payments/{payment_id}/confirm`, `PATCH /{booking_id}/cancel`, `GET /my-bookings` |
| `/subscriptions` | `GET /plans`, `POST /purchase`, `PATCH /{subscription_id}/freeze`, `GET /my-subscriptions`, management CRUD |
| `/payments` | `POST /checkout`, `GET /my-payments`, `GET /` |
| `/reports` | `GET /revenue`, `GET /trainers/popularity` |
| `/public` | `GET /club-stats`, `GET /membership-plans` |
| `/health` | `GET /live`, `GET /ready` |

## DTO та валідація

- Для вхідних і вихідних контрактів використано `Pydantic v2`.
- API не повертає сирі ORM-моделі напряму.
- Приклади DTO:
  - `AuthPayload`
  - `UserRead`
  - `ScheduleRead`
  - `SubscriptionRead`
  - `PaymentRead`
  - `RevenueReport`

## Приклад реалізації потоку

1. Клієнт викликає `POST /subscriptions/purchase`.
2. Роутер валідовує тіло запиту і викликає `SubscriptionService`.
3. Сервіс перевіряє наявність активного абонемента і підбирає план.
4. Через `PaymentService` створюється платіжний запис.
5. Репозиторії та ORM зберігають зміни в PostgreSQL.
6. API повертає DTO `SubscriptionRead`.

## Інструменти тестування

- `pytest` для інтеграційних та unit-тестів.
- `httpx` / `TestClient` для перевірки маршрутів.
- Swagger UI для ручного тестування REST API.

Актуальний результат перевірки на 2026-03-25:

- `50/50` backend-тестів проходять успішно.
- покриття коду бекенду: `87%`.

## Короткі відповіді для захисту

1. REST у цьому проєкті обрано через простий HTTP-контракт і вбудовану документацію Swagger.
2. DTO захищають клієнта від витоку внутрішньої структури ORM-моделей.
3. Idempotent-операціями мають бути безпечні повторні `GET`, а також коректно спроєктовані `PUT`/`DELETE`.
4. Валідація на рівні схем дає передбачувані `400/422` відповіді замість випадкових помилок сервера.

## Висновок

У межах Лабораторної №3 бекенд реалізовано як повноцінний REST API з DAL,
service layer, dependency injection та DTO-контрактами. Отриманий API став базою
для подальшої реалізації безпеки та фронтенд-інтеграції.

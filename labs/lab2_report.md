# Лабораторна робота №2

## Тема

Проєктування архітектури програмного забезпечення та моделювання даних для
**Fitness Club Management System**.

## Мета роботи

Обґрунтувати вибір стеку, описати архітектуру системи за моделлю C4 та побудувати
схему даних, яка покриває основні доменні сутності клубу.

## Обраний технологічний стек

| Шар | Технології | Обґрунтування |
|---|---|---|
| Backend | FastAPI, Pydantic v2 | швидка побудова typed REST API та Swagger/OpenAPI з коробки |
| ORM | SQLAlchemy 2.0 Async | чіткий контроль моделі даних і транзакцій |
| Міграції | Alembic | версіонування схеми БД і контроль змін |
| БД | PostgreSQL | надійна реляційна БД для транзакційних сценаріїв |
| Cache / sessions | Redis | зберігання сесій, rate limit, revoke flow |
| Background jobs | Celery + Celery Beat | запуск reminder- та maintenance-задач |
| Frontend | React 19 + TypeScript + Vite | швидкий SPA-стек з суворою типізацією |
| Client state | Zustand | компактний store для auth/session |
| Server state | TanStack Query | кешування, refetch та інвалідація даних |
| DevOps | Docker Compose | простий локальний запуск усіх сервісів |

## C4: System Context

```mermaid
flowchart LR
    client[Клієнт]
    trainer[Тренер]
    admin[Адміністратор]
    owner[Власник]
    system[Fitness Club Management System]
    postgres[(PostgreSQL)]
    redis[(Redis)]

    client --> system
    trainer --> system
    admin --> system
    owner --> system
    system --> postgres
    system --> redis
```

Система є єдиною точкою взаємодії для всіх ролей і працює поверх PostgreSQL та Redis.

## C4: Container Diagram

```mermaid
flowchart LR
    browser[React SPA<br/>Vite + TypeScript]
    api[FastAPI API<br/>routers/services/repositories]
    worker[Celery Worker]
    beat[Celery Beat]
    postgres[(PostgreSQL)]
    redis[(Redis)]

    browser <-- HTTP/JSON --> api
    api <-- SQLAlchemy --> postgres
    api <-- sessions/cache --> redis
    worker <-- queue/state --> redis
    worker <-- SQL --> postgres
    beat --> worker
```

Контейнери розділено так, щоб окремо масштабувати web, API і фон.

## C4: Component Diagram для API Application

```mermaid
flowchart TD
    routes[API Routes]
    deps[API Dependencies]
    services[Service Layer]
    repos[Repository Layer]
    schemas[Schemas / DTO]
    models[SQLAlchemy Models]
    middleware[Middleware]
    core[Core Security / Config / Redis]
    db[(PostgreSQL)]
    redis[(Redis)]

    routes --> deps
    routes --> schemas
    routes --> services
    middleware --> routes
    services --> repos
    services --> core
    repos --> models
    repos --> db
    core --> redis
```

Уся складна логіка винесена з роутів у сервіси, а доступ до БД ізольований у репозиторіях.

## ER-модель

```mermaid
erDiagram
    USER ||--o{ SUBSCRIPTION : owns
    USER ||--o{ PAYMENT : makes
    USER ||--o{ BOOKING : creates
    USER ||--o{ WORKOUT_CLASS : teaches
    MEMBERSHIP_PLAN ||--o{ SUBSCRIPTION : defines
    WORKOUT_CLASS ||--o{ BOOKING : contains

    USER {
        string id PK
        string email UK
        string password_hash
        string role
        string first_name
        string last_name
        string phone
        boolean is_verified
    }

    MEMBERSHIP_PLAN {
        string id PK
        string title
        string type
        int duration_days
        int visits_limit
        decimal price
        string currency
        boolean is_active
        boolean is_public
    }

    SUBSCRIPTION {
        string id PK
        string user_id FK
        string plan_id FK
        string type
        datetime start_date
        datetime end_date
        string status
        int total_visits
        int remaining_visits
    }

    WORKOUT_CLASS {
        string id PK
        string trainer_id FK
        string title
        datetime start_time
        datetime end_time
        int capacity
        string type
        boolean is_paid_extra
        decimal extra_price
    }

    BOOKING {
        string id PK
        string user_id FK
        string class_id FK
        string status
    }

    PAYMENT {
        string id PK
        string user_id FK
        decimal amount
        string status
        string method
        string purpose
        string booking_class_id
    }
```

## Нормалізація та ключові індекси

- `users.email` - унікальний індекс для логіну.
- `workout_classes.start_time` - швидкий пошук розкладу.
- `subscriptions.status` і `subscriptions.end_date` - звіти та reminder-задачі.
- `bookings(user_id, class_id)` - захист від дубльованого бронювання.
- `payments.created_at` - історія платежів і звіти.

## Короткі відповіді для захисту

1. C4 показує систему на трьох рівнях деталізації: контекст, контейнери й компоненти.
2. PostgreSQL обрано через транзакційність і чіткі зв'язки між сутностями.
3. CAP вказує, що у розподіленій системі неможливо одночасно максимізувати консистентність, доступність і стійкість до мережевого розділення.
4. Для цього проєкту modular monolith кращий за мікросервіси, бо дає нижчу складність при достатній масштабованості.

## Висновок

На етапі Лабораторної №2 сформовано цілісну архітектурну модель системи.
Обраний стек напряму підтримує транзакційні сценарії клубу, а C4- і ER-діаграми
узгоджують вимоги Лабораторної №1 з реальною структурою коду.

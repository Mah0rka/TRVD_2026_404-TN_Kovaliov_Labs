# Fitness Club Management System

Вебзастосунок для керування фітнес-клубом з окремими модулями `backend` і `frontend`.

## Структура репозиторію

- `backend` - FastAPI, SQLAlchemy 2.0, Alembic, Redis, Celery, pytest.
- `frontend` - React 19, TypeScript, React Router, TanStack Query, Zustand, Vitest.
- `Docs` - окрема технічна документація для бекенду й фронтенду.
- `labs` - звіти до лабораторних робіт 1-5 та вихідні PDF з умовами.
- `scripts` - скрипти швидкої локальної перевірки.

## Швидкий старт

### Запуск у Docker

```bash
docker compose up --build
```

Сервіси після старту:

- frontend: `http://localhost:3000`
- backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`

## Документація

- [Backend Guide](backend/Docs/backend.md)
- [Frontend Guide](frontend/Docs/frontend.md)
- [Lab Reports Index](labs/README.md)


## Ліцензія

Цей репозиторій є source-available.

- Перегляд, форк і модифікація дозволені для особистого та навчального використання.
- Комерційне використання, продаж або надання як SaaS заборонені без письмового дозволу автора.
- Деталі комерційного ліцензування наведені у `COMMERCIAL_LICENSE.md`.

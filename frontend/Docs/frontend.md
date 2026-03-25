# Frontend Documentation

## Огляд

`frontend` - це SPA на `React 19 + TypeScript`, яка працює поверх захищеного API.
Клієнтська частина забезпечує логін, відновлення сесії, захищені маршрути,
перегляд розкладу, бронювання, роботу з абонементами, оплатами, звітами та
адміністративними сторінками.

## Технологічний стек

| Категорія | Технології |
|---|---|
| UI | React 19, TypeScript, CSS |
| Router | React Router |
| Server state | TanStack Query |
| Client state | Zustand |
| Валідація контрактів | Zod |
| Тести | Vitest, Testing Library, jsdom |

## Структура фронтенду

| Папка | Призначення |
|---|---|
| `src/app` | bootstrap, роутер, провайдери |
| `src/features` | бізнес-фічі, сторінки та feature-specific UI |
| `src/shared/api` | HTTP-клієнт, контракти API, модулі запитів |
| `src/shared/ui` | спільні UI-компоненти |
| `src/shared/lib` | утиліти |
| `src/test` | тестові helper-функції |

## Основні сторінки

| Маршрут | Призначення | Доступ |
|---|---|---|
| `/` | маркетингова головна сторінка | public |
| `/login` | форма входу | public only |
| `/dashboard` | загальний огляд системи | authenticated |
| `/dashboard/profile` | профіль користувача | authenticated |
| `/dashboard/schedule` | розклад клубу | authenticated |
| `/dashboard/bookings` | мої записи | client |
| `/dashboard/subscriptions` | абонементи | client, admin, owner |
| `/dashboard/payments` | історія оплат | client, admin, owner |
| `/dashboard/my-classes` | заняття тренера | trainer |
| `/dashboard/users` | керування учасниками | admin, owner |
| `/dashboard/reports` | аналітика | admin, owner |

## Робота з API

1. Усі запити проходять через `shared/api/core/http.ts`.
2. `fetch` викликається тільки в API-шарі, а не в компонентах.
3. Для mutating-запитів автоматично додається `X-CSRF-Token`.
4. При `401` клієнт намагається оновити сесію через `/auth/refresh`.
5. Якщо refresh не вдався, UI отримує подію `fcms:auth-expired` і розлогінює користувача.

## Стан застосунку

- `Zustand` зберігає `user`, `isAuthenticated`, `isReady`.
- `AuthBootstrap` на старті перевіряє cookie-підказку та викликає `/auth/me`.
- `ProtectedLayout` і `PublicOnlyLayout` керують доступом до маршрутів.
- `RoleBoundary` обмежує ролі на рівні роутів і UI-навігації.

## UX-принципи

- Інтерфейс локалізований українською.
- Сторінки використовують loading/error/empty states.
- Контракти API валідовані через `Zod`.
- Навігація адаптується під роль користувача.
- CRUD-сценарії мають інвалідацію запитів через `TanStack Query`.

## Запуск

### Docker

```bash
docker compose up --build frontend backend
```

### Локально

```bash
cd frontend
npm install
npm run dev
```

За замовчуванням дев-сервер працює на `http://localhost:3000`.

## Тестування

```powershell
./scripts/test-frontend.ps1
```

Актуальний стан перевірки на 2026-03-25:

- `60/60` frontend-тестів проходять успішно.
- покриття фронтенду: `85.92%`.

## Корисні точки входу

- `frontend/src/main.tsx` - bootstrap React-застосунку.
- `frontend/src/app/routes.tsx` - карта маршрутів і lazy-loading сторінок.
- `frontend/src/features/auth/ui/AuthBootstrap.tsx` - відновлення сесії.
- `frontend/src/shared/api/core/http.ts` - базовий HTTP-клієнт.
- `frontend/src/features/users/pages/UsersPage.tsx` - найбільший management CRUD flow.

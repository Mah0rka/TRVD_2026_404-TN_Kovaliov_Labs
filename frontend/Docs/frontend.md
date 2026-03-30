# Frontend Documentation

## Огляд

`frontend` - це SPA на `React 19 + TypeScript`, яка працює поверх cookie-based API.
Клієнтська частина покриває логін, відновлення сесії, захищені маршрути,
розклад занять, бронювання, абонементи, оплати, звіти та management-сценарії.

## Технологічний стек

| Категорія | Технології |
|---|---|
| UI | React 19, TypeScript, CSS |
| Router | React Router |
| Server state | TanStack Query |
| Client state | Zustand |
| Валідація контрактів | Zod |
| Тести | Vitest, Testing Library, jsdom |

## Архітектурні шари

| Папка | Призначення |
|---|---|
| `src/app` | bootstrap, роутер, провайдери, глобальні layout-boundaries |
| `src/features` | бізнес-фічі, сторінки, role-aware hooks, navigation shell |
| `src/shared/api` | HTTP-клієнт, API-контракти, модулі запитів, централізовані query keys |
| `src/shared/ui` | справді спільні UI-примітиви без залежностей на бізнес-фічі |
| `src/shared/lib` | утиліти та дрібні helper-функції |
| `src/styles` | модульні CSS partials і vendor overrides |
| `src/test` | тестові helper-функції |

Поточний напрямок залежностей такий:

1. `app` і feature-shells можуть збирати сторінки та навігацію.
2. `features` працюють поверх `shared`.
3. `shared` не імпортує `features`.

Додатково варто тримати в голові таке практичне правило:

- `page`-компонент має збирати екран і керувати локальним UI-станом.
- `hook` у feature-шарі має забирати на себе fetch/mutation wiring.
- `shared/api` має залишатися єдиним місцем прямої роботи з HTTP.
- `lib`-helper-и повинні бути чистими настільки, наскільки це можливо, щоб їх було легко тестувати.

Цей розподіл уже помітний у `dashboard`, `subscriptions`, `classes` і `schedules`: сторінки рендерять, hooks домовляються з сервером, а helper-и трансформують дані у форму, зручну для UI.

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
| `/dashboard/my-classes` | заняття тренера, історія класів і підтвердження завершення | trainer, admin, owner |
| `/dashboard/users` | керування учасниками | admin, owner |
| `/dashboard/reports` | аналітика | admin, owner |

## Робота з API

1. Усі HTTP-виклики проходять через `src/shared/api/core/http.ts`.
2. `fetch` використовується лише в API-шарі, а не в компонентах.
3. Для mutating-запитів клієнт автоматично додає `X-CSRF-Token`.
4. При `401` HTTP-клієнт пробує оновити сесію через `/auth/refresh`.
5. Якщо refresh не вдається, UI отримує подію `fcms:auth-expired` і розлогінює користувача.

### Повний цикл запиту

Щоб швидше орієнтуватися в коді, корисно дивитися на типовий життєвий цикл даних:

1. Сторінка або feature-hook викликає функцію з `src/shared/api/modules/*`.
2. Ця функція йде через `request<T>()` з `src/shared/api/core/http.ts`.
3. `request<T>()` додає `credentials`, CSRF-заголовки та обробку refresh-сценарію.
4. `TanStack Query` кешує результат під ключем із `src/shared/api/queryKeys.ts`.
5. Після mutation feature-hook централізовано інвалідовує всі surface-и, яким потрібен свіжий зріз даних.
6. Page-компонент або view-model вже рендерить готовий результат без прямої роботи з HTTP.

Такий ланцюжок важливий для підтримки: якщо у UI показуються застарілі дані, перевіряти потрібно не лише компонент, а й відповідний query key та invalidation policy.

### Контракти та query keys

- API-контракти розбиті по доменах у `src/shared/api/contracts/*`.
- `src/shared/api/core/contracts.ts` зберігає сумісний barrel-export.
- `src/shared/api/queryKeys.ts` є єдиним джерелом правди для TanStack Query keys.
- Сторінки не повинні задавати cache keys вручну рядками.

## Стан застосунку

- `Zustand` зберігає `user`, `isAuthenticated`, `isReady`.
- `AuthBootstrap` на старті перевіряє session hint і викликає `/auth/me`, якщо сесія схожа на живу.
- `ProtectedLayout` і `PublicOnlyLayout` керують доступом до маршрутів.
- `RoleBoundary` обмежує ролі на рівні роутів і UI-навігації.
- `DashboardShell` тепер живе у feature-шарі навігації, а не в `shared/ui`.

### Auth lifecycle детальніше

Поведінка авторизації побудована так, щоб уникнути фальшивих редіректів на холодному старті:

1. `AuthBootstrap` монтується над усім route tree.
2. Якщо в браузері немає `fcms_csrf_token`, застосунок одразу переходить у `isReady=true` без `/auth/me`.
3. Якщо session hint є, фронтенд робить `/auth/me` і синхронізує `Zustand`-store.
4. Поки цей процес триває, `ProtectedLayout` не приймає рішення про redirect.
5. Якщо API-клієнт вичерпав refresh-сценарій, він викидає подію `fcms:auth-expired`, а `AuthBootstrap` очищає auth-state.

Саме зв'язка `AuthBootstrap` + `ProtectedLayout` + `request<T>()` формує повний auth flow. Якщо змінювати один із цих елементів, варто завжди перевіряти решту двох.

## Роутинг і доступ

Маршрути в `src/app/routes.tsx` спеціально організовані як набір вкладених guard/layout-рівнів:

- `AuthBootstrap` огортає все дерево.
- `PublicOnlyLayout` не пускає авторизованого користувача на `/login`.
- `ProtectedLayout` дає dashboard shell тільки після завершеного auth bootstrap.
- `RoleBoundary` використовується для сегментів, де роль впливає на доступ до цілої сторінки, а не лише до окремої кнопки.

Практичний наслідок: якщо нова сторінка має бути доступна лише певним ролям, правильне місце для правила зазвичай у `routes.tsx`, а не глибоко всередині JSX сторінки.

## Великі feature-flows

### Dashboard

- `DashboardPage` є thin renderer.
- `useDashboardData` виконує role-aware queries.
- `buildDashboardViewModel` перетворює сирі дані на hero/stat/link блоки.

Це зроблено свідомо: dashboard є композиційним екраном, де один і той самий layout обслуговує кілька ролей. Якщо дати сторінці самій вирішувати, які endpoint-и запитувати й як будувати картки, вона швидко перетвориться на великий умовний рендер із переплетеною бізнес-логікою.

### Schedule

- `SchedulePage` є role-switch між двома окремими екранами.
- `ClientScheduleView` рендерить список доступних занять і booking/payment flow.
- `StaffScheduleView` містить FullCalendar, редактор занять і attendee flow.
- Staff-view lazy-load'иться окремим chunk'ом, тому клієнтський список не тягне важкий календарний стек.

#### Що важливо про schedule-flow

- `SchedulePage` не містить бізнес-логіки, а лише вирішує, який UX потрібен ролі.
- `ClientScheduleView` працює з картками, фільтрами і pending checkout state для платних занять.
- `StaffScheduleView` тримає робочий календар, range-based fetch і modal editor.
- `scheduleShared.tsx` містить перетворення дат, recurrence helper-и, form defaults і валідацію.
- `ScheduleEditorModal.tsx` залишається максимально "тупою" відносно API: він отримує вже готовий `editorState`, права і callback-и зверху.

Такий split особливо корисний тут, бо schedule-flow має дві зовсім різні моделі взаємодії: "я хочу записатись" і "я керую клубним розкладом".

### Classes та Subscriptions

- `MyClassesPage` використовує `useClassesPageData` для queries, mutations та invalidation policy.
- `SubscriptionsPage` використовує `useSubscriptionsPageData` для plans/purchase/freeze/admin mutations.
- Інвалідація пов'язаних surfaces виконується в feature-hooks, а не розсипана по JSX.

#### Classes-flow

- `MyClassesPage` ділить один dataset на `ACTIVE`, `PENDING` і `HISTORY`.
- Права панель показує або список учасників, або підсумок завершеного заняття.
- Завершення заняття оновлює не лише classes-екран, а й dashboard/schedule surface-и, які читають той самий клас з інших query namespace-ів.

#### Subscriptions-flow

- Один і той самий екран обслуговує клієнтський і management-сценарій.
- Клієнт бачить каталог планів, власні абонементи та freeze-flow.
- Менеджмент бачить CRUD для membership plans і службову навігацію до `Users`.
- Invalidation policy у hook-у критична, бо купівля абонемента змінює ще й payments/dashboard.

## Стилі

CSS більше не збирається через монолітний `legacy.css`.

- `src/styles.css` є єдиним entrypoint для глобальних partials.
- `src/styles/tokens.css` містить font import, theme variables і document-level primitives.
- `src/styles/base.css` містить спільні surface, form і button стилі.
- `src/styles/layout.css` покриває app shell, sidebar, topbar і workspace layout.
- `src/styles/dashboard.css`, `src/styles/marketing.css`, `src/styles/management.css`, `src/styles/classes.css` розносять великі UI-зони по окремих partials.
- `src/styles/schedule.css` відповідає за schedule/classes presentation layer.
- `src/styles/responsive.css` містить спільні responsive overrides.
- `src/styles/vendor/fullcalendar.css` зберігає лише FullCalendar-specific overrides.

Такий split прибирає single-source CSS моноліт і дає зрозуміліші точки входу для подальшого доопрацювання `dashboard`, `marketing` і management-екранів.

## UX-принципи

- Інтерфейс локалізований українською.
- Сторінки використовують loading, error та empty states.
- Контракти API валідовані через `Zod`.
- Навігація адаптується під роль користувача.
- CRUD-сценарії мають централізовану invalidation policy через `TanStack Query`.
- Кожна dashboard-сторінка має один основний заголовок і коротке пояснення без дубльованих шапок.

## Принципи коментування коду

Фронтенд уже не потребує коментарів на кшталт "ця функція повертає значення". Корисними вважаються інші типи пояснень:

- чому query увімкнена лише для певної ролі;
- чому після mutation інвалідовується кілька різних cache key;
- чому schedule/staff flow lazy-loadиться окремо;
- як пов'язані локальний form-state, backend payload і recurrence scope;
- чому layout або route guard приймає рішення саме в цій точці дерева.

Якщо новий коментар не пояснює причину, наслідок або нетривіальне обмеження, його краще не додавати.

## Куди дивитися під час змін

- Якщо змінюється access control: перевіряти `src/app/routes.tsx`, `AuthBootstrap`, `ProtectedLayout`, `RoleBoundary`.
- Якщо змінюється fetch/mutation flow: перевіряти `shared/api/modules/*`, `shared/api/core/http.ts`, `queryKeys.ts`, feature-hook.
- Якщо змінюється schedule recurring: перевіряти `scheduleShared.tsx`, `StaffScheduleView.tsx`, `ScheduleEditorModal.tsx`.
- Якщо змінюється dashboard summary: перевіряти `useDashboardData.ts` і `buildDashboardViewModel`.
- Якщо дані оновилися на сервері, але не в UI: шукати пропущену `invalidateQueries`.

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

За замовчуванням dev-сервер працює на `http://localhost:3000`.

## Тестування

### Основні команди

```bash
cd frontend
npm run test:run
npm run test:coverage
npm run build
```

### PowerShell-скрипт

```powershell
./scripts/test-frontend.ps1
```

### Останній підтверджений локальний прогін

Стан на `2026-03-29`:

- `npm run test:run` -> `23/23` test files, `67/67` tests passed.
- `./scripts/test-frontend.ps1` -> coverage `83.57%` statements, `74.77%` branches, `77.75%` functions, `85.05%` lines.
- `npm run build` -> production build проходить успішно.
- Build підтверджує окремий staff-chunk: `dist/assets/StaffScheduleView-*.js`.

## Корисні точки входу

- `frontend/src/main.tsx` - bootstrap React-застосунку.
- `frontend/src/app/routes.tsx` - карта маршрутів і lazy-loading сторінок.
- `frontend/src/features/auth/ui/AuthBootstrap.tsx` - відновлення сесії.
- `frontend/src/features/navigation/ui/DashboardShell.tsx` - dashboard shell і навігація.
- `frontend/src/shared/api/core/http.ts` - базовий HTTP-клієнт.
- `frontend/src/shared/api/queryKeys.ts` - централізовані query keys.
- `frontend/src/features/schedules/pages/SchedulePage.tsx` - role-aware вхід у schedule-flow.
- `frontend/src/features/users/pages/UsersPage.tsx` - management CRUD flow.
- `frontend/src/features/classes/pages/MyClassesPage.tsx` - тренерський і management flow завершення занять.

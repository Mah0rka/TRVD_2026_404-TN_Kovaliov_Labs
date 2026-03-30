# Frontend Quick Guide

## Як працювати

- Працюй у `frontend/src`.
- Нову бізнес-логіку клади в `features/<feature>`.
- API викликай тільки через `shared/api`.
- Для кешу використовуй `shared/api/queryKeys.ts`.
- Сторінки тримай thin, логіку винось у `hooks` і `lib`.

## Як масштабувати

- Зберігай напрямок: `app -> features -> shared`.
- Не імпортуй `features` у `shared`.
- Розбивай великі фічі на `pages`, `hooks`, `ui`, `lib`.
- Стилі додавай у відповідний partial у `src/styles`.
- Після змін перевіряй `npm run test:run` і `npm run build`.

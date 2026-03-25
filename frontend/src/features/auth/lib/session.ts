// Модуль містить допоміжну логіку для конкретної фічі.

// Перевіряє, чи є в браузері ознака активної auth-сесії.
export function hasSessionHint(): boolean {
  return document.cookie.split("; ").some((entry) => entry.startsWith("fcms_csrf_token="));
}

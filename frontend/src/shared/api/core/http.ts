// Модуль описує базову логіку клієнтського API-шару.

const configuredBaseUrl = import.meta.env.VITE_API_URL?.trim() ?? "";
const API_BASE_URL = import.meta.env.DEV ? "" : configuredBaseUrl;
export const AUTH_EXPIRED_EVENT = "fcms:auth-expired";

let refreshPromise: Promise<boolean> | null = null;

export class ApiError extends Error {
  status: number;
  requestId?: string;

  // Ініціалізує об'єкт помилки з HTTP-статусом і request id.
  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

// Зчитує CSRF token з cookies браузера.
function readCsrfToken(): string | null {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith("fcms_csrf_token="));

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

// Готує заголовки запиту та додає CSRF token для mutating-викликів.
function buildHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers);

  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (init?.method && !["GET", "HEAD"].includes(init.method.toUpperCase())) {
    const csrfToken = readCsrfToken();
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  return headers;
}

// Пробує оновити авторизаційну сесію через refresh endpoint.
async function refreshSession(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: buildHeaders({ method: "POST" })
      });

      return response.ok;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

// Сповіщає застосунок про завершення сесії користувача.
function notifyAuthExpired() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
  }
}

// Виконує HTTP-запит, обробляє 401 і піднімає типізовану помилку API.
export async function request<T>(
  path: string,
  init?: RequestInit,
  options: { retryOnAuth?: boolean } = {}
): Promise<T> {
  let authExpiredNotified = false;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: buildHeaders(init),
    credentials: "include"
  });

  const isRefreshEligiblePath = ![
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/logout"
  ].includes(path);

  if (response.status === 401 && options.retryOnAuth !== false && isRefreshEligiblePath) {
    const refreshed = await refreshSession();
    if (refreshed) {
      return request<T>(path, init, { retryOnAuth: false });
    }
    notifyAuthExpired();
    authExpiredNotified = true;
  }

  if (!response.ok) {
    if (response.status === 401 && isRefreshEligiblePath && !authExpiredNotified) {
      notifyAuthExpired();
    }

    const errorBody = await response
      .json()
      .catch(() => ({ detail: "Request failed", request_id: undefined }));

    throw new ApiError(
      errorBody.detail ?? "Request failed",
      response.status,
      errorBody.request_id
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

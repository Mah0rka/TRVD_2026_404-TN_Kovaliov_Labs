// HTTP-клієнт є єдиною точкою доступу до backend API.
// Тут зосереджені три критичні правила:
// - dev/prod base URL стратегія;
// - CSRF-підпис mutating-запитів;
// - автоматичний refresh/retry для 401 без розмазування цієї логіки по feature-коду.

const configuredBaseUrl = import.meta.env.VITE_API_URL?.trim() ?? "";
// У dev середовищі лишаємо відносні шляхи, щоб Vite proxy міг прозоро
// прокидати `/auth`, `/schedules` та інші endpoint-и на backend.
const API_BASE_URL = import.meta.env.DEV ? "" : configuredBaseUrl;
export const AUTH_EXPIRED_EVENT = "fcms:auth-expired";

// Один спільний promise не дає кільком паралельним 401 одночасно запускати
// декілька refresh-запитів і змагатися між собою за стан сесії.
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

// CSRF token читається з cookie, яку видає backend. Саме cookie лишається
// доступною JS, бо значення токена треба дублювати в X-CSRF-Token заголовок.
function readCsrfToken(): string | null {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith("fcms_csrf_token="));

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

// Базові заголовки будуються централізовано, щоб feature-модулі не думали
// про Content-Type і CSRF при кожному виклику request().
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

// Refresh викликаємо лише через цей helper, щоб легко гарантувати dedupe та
// однакові credentials/headers для всіх повторних спроб.
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

// DOM-подія є тонким контрактом між API-шаром і React-auth bootstrap-ом.
function notifyAuthExpired() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
  }
}

// request<T>() інкапсулює весь happy path і error path:
// - виконує fetch;
// - при дозволеному 401 пробує refresh;
// - повторює оригінальний запит один раз;
// - піднімає ApiError з detail/request_id для UI.
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

  // Для auth-endpoint-ів retry був би небезпечний або беззмістовний:
  // login/register/logout/refresh мають власну семантику і не повинні
  // автоматично запускати ще один refresh поверх себе.
  const isRefreshEligiblePath = ![
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/logout"
  ].includes(path);

  if (response.status === 401 && options.retryOnAuth !== false && isRefreshEligiblePath) {
    const refreshed = await refreshSession();
    if (refreshed) {
      // Рекурсивний повтор відбувається лише один раз завдяки retryOnAuth=false,
      // тому нескінченного циклу refresh -> retry -> refresh тут не буде.
      return request<T>(path, init, { retryOnAuth: false });
    }
    notifyAuthExpired();
    authExpiredNotified = true;
  }

  if (!response.ok) {
    if (response.status === 401 && isRefreshEligiblePath && !authExpiredNotified) {
      notifyAuthExpired();
    }

    // Намагаємось прочитати backend detail/request_id, але не падаємо вдруге,
    // якщо тіло відповіді не є JSON.
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
    // Для DELETE/empty-success endpoint-ів повертаємо undefined, зберігаючи
    // при цьому єдиний generic-інтерфейс request<T>().
    return undefined as T;
  }

  return (await response.json()) as T;
}

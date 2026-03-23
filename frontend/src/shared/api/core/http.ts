const configuredBaseUrl = import.meta.env.VITE_API_URL?.trim() ?? "";
const API_BASE_URL =
  import.meta.env.DEV && typeof window !== "undefined" && window.location.port === "3000"
    ? ""
    : configuredBaseUrl;

let refreshPromise: Promise<boolean> | null = null;

export class ApiError extends Error {
  status: number;
  requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

function readCsrfToken(): string | null {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith("fcms_csrf_token="));

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

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

export async function request<T>(
  path: string,
  init?: RequestInit,
  options: { retryOnAuth?: boolean } = {}
): Promise<T> {
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
  }

  if (!response.ok) {
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

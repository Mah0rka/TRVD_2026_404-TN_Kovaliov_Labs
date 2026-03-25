// Тести перевіряють ключові сценарії цього модуля.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, request } from "./http";

describe("request", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    document.cookie = "fcms_csrf_token=test-token";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    document.cookie = "fcms_csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
  });

  it("sends JSON request with csrf header", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ ok: true })
    });

    const result = await request<{ ok: boolean }>("/example", {
      method: "POST",
      body: JSON.stringify({ value: 1 })
    });

    expect(result).toEqual({ ok: true });
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.credentials).toBe("include");
    expect((init.headers as Headers).get("Content-Type")).toBe("application/json");
    expect((init.headers as Headers).get("X-CSRF-Token")).toBe("test-token");
  });

  it("returns undefined for 204 response", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: async () => ({})
    });

    const result = await request<void>("/empty", { method: "DELETE" });

    expect(result).toBeUndefined();
  });

  it("refreshes session and retries once on 401", async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({})
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ value: "ok" })
      });

    const result = await request<{ value: string }>("/protected", { method: "GET" });

    expect(result).toEqual({ value: "ok" });
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/auth/refresh",
      expect.objectContaining({
        method: "POST",
        credentials: "include"
      })
    );
  });

  it("does not refresh auth endpoints and throws ApiError", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Bad credentials", request_id: "req-1" })
    });

    await expect(
      request("/auth/login", { method: "POST" }, { retryOnAuth: false })
    ).rejects.toEqual(new ApiError("Bad credentials", 401, "req-1"));

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws fallback ApiError when error body is invalid", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("bad json");
      }
    });

    await expect(request("/broken", { method: "GET" })).rejects.toEqual(
      new ApiError("Request failed", 500, undefined)
    );
  });
});

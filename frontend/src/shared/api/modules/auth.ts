// Коротко: модуль виконує API-запити для модуля автентифікації.

import type { CurrentUser } from "../core/contracts";
import { authResponseSchema, userSchema } from "../core/contracts";
import { request } from "../core/http";

export async function login(email: string, password: string): Promise<CurrentUser> {
  const data = await request<unknown>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password })
    },
    { retryOnAuth: false }
  );

  return authResponseSchema.parse(data).user;
}

export async function register(input: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}): Promise<CurrentUser> {
  const data = await request<unknown>(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify(input)
    },
    { retryOnAuth: false }
  );

  return authResponseSchema.parse(data).user;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const data = await request<unknown>("/auth/me", { method: "GET" });
  return userSchema.parse(data);
}

export async function logout(): Promise<void> {
  await request("/auth/logout", { method: "POST" }, { retryOnAuth: false });
}

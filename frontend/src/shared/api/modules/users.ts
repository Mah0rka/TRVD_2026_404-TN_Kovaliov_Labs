// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { CurrentUser, PaginatedUsers, UserRole } from "../core/contracts";
import { paginatedUsersSchema, userSchema } from "../core/contracts";
import { request } from "../core/http";

// Надсилає на бекенд зміни профілю поточного користувача.
export async function updateMyProfile(input: {
  first_name?: string;
  last_name?: string;
  phone?: string | null;
}): Promise<CurrentUser> {
  const data = await request<unknown>("/users/profile", {
    method: "PATCH",
    body: JSON.stringify(input)
  });

  return userSchema.parse(data);
}

// Отримує список користувачів з необовʼязковим фільтром за роллю.
export async function getUsers(role?: UserRole): Promise<CurrentUser[]> {
  const params = new URLSearchParams();
  if (role) {
    params.set("role", role);
  }

  const data = await request<unknown>(`/users${params.size ? `?${params.toString()}` : ""}`, {
    method: "GET"
  });

  return z.array(userSchema).parse(data);
}

// Отримує сторінку користувачів для клієнтської пагінації.
export async function getUsersPage(input?: {
  role?: UserRole;
  page?: number;
  pageSize?: number;
}): Promise<PaginatedUsers> {
  const params = new URLSearchParams();
  if (input?.role) {
    params.set("role", input.role);
  }
  params.set("page", String(input?.page ?? 1));
  params.set("page_size", String(input?.pageSize ?? 10));

  const data = await request<unknown>(`/users/paginated?${params.toString()}`, {
    method: "GET"
  });

  return paginatedUsersSchema.parse(data);
}

// Створює користувача через API адмін-панелі.
export async function createUser(input: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  is_verified?: boolean;
}): Promise<CurrentUser> {
  const data = await request<unknown>("/users", {
    method: "POST",
    body: JSON.stringify(input)
  });

  return userSchema.parse(data);
}

// Оновлює користувача через API адмін-панелі.
export async function updateUser(
  userId: string,
  input: {
    email?: string;
    password?: string;
    first_name?: string;
    last_name?: string;
    phone?: string | null;
    role?: UserRole;
    is_verified?: boolean;
  }
): Promise<CurrentUser> {
  const data = await request<unknown>(`/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(input)
  });

  return userSchema.parse(data);
}

// Видаляє користувача через API адмін-панелі.
export async function deleteUser(userId: string): Promise<void> {
  await request<void>(`/users/${userId}`, {
    method: "DELETE"
  });
}

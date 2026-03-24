import { z } from "zod";

import type { CurrentUser, UserRole } from "../core/contracts";
import { userSchema } from "../core/contracts";
import { request } from "../core/http";

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

export async function deleteUser(userId: string): Promise<void> {
  await request<void>(`/users/${userId}`, {
    method: "DELETE"
  });
}

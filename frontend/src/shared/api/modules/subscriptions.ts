// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { MembershipPlan, Subscription } from "../core/contracts";
import { membershipPlanSchema, subscriptionSchema } from "../core/contracts";
import { request } from "../core/http";

// Отримує абонементи поточного користувача.
export async function getSubscriptions(): Promise<Subscription[]> {
  const data = await request<unknown>("/subscriptions/my-subscriptions", { method: "GET" });
  return z.array(subscriptionSchema).parse(data);
}

// Отримує абонементи для management-перегляду з фільтрами.
export async function getManagedSubscriptions(input?: {
  userId?: string;
  includeDeleted?: boolean;
}): Promise<Subscription[]> {
  const params = new URLSearchParams();
  if (input?.userId) {
    params.set("user_id", input.userId);
  }
  if (input?.includeDeleted) {
    params.set("include_deleted", "true");
  }

  const data = await request<unknown>(`/subscriptions${params.size ? `?${params.toString()}` : ""}`, {
    method: "GET"
  });
  return z.array(subscriptionSchema).parse(data);
}

// Отримує список доступних планів абонементів.
export async function getSubscriptionPlans(): Promise<MembershipPlan[]> {
  const data = await request<unknown>("/subscriptions/plans", { method: "GET" });
  return z.array(membershipPlanSchema).parse(data);
}

// Оформлює купівлю вибраного плану абонемента.
export async function purchaseSubscription(planId: string): Promise<Subscription> {
  const data = await request<unknown>("/subscriptions/purchase", {
    method: "POST",
    body: JSON.stringify({ plan_id: planId })
  });

  return subscriptionSchema.parse(data);
}

// Надсилає запит на заморозку абонемента.
export async function freezeSubscription(id: string, days: number): Promise<Subscription> {
  const data = await request<unknown>(`/subscriptions/${id}/freeze`, {
    method: "PATCH",
    body: JSON.stringify({ days })
  });

  return subscriptionSchema.parse(data);
}

// Оновлює абонемент у management-сценарії через API.
export async function updateClientSubscription(
  id: string,
  payload: {
    plan_id?: string;
    start_date?: string;
    end_date?: string;
    status?: "ACTIVE" | "FROZEN" | "EXPIRED";
    total_visits?: number | null;
    remaining_visits?: number | null;
  }
): Promise<Subscription> {
  const data = await request<unknown>(`/subscriptions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });

  return subscriptionSchema.parse(data);
}

// Видаляє абонемент у management-сценарії через API.
export async function deleteClientSubscription(id: string): Promise<void> {
  await request<void>(`/subscriptions/${id}`, {
    method: "DELETE"
  });
}

// Відновлює видалений абонемент через API.
export async function restoreClientSubscription(id: string): Promise<Subscription> {
  const data = await request<unknown>(`/subscriptions/${id}/restore`, {
    method: "POST"
  });

  return subscriptionSchema.parse(data);
}

// Видає абонемент клієнту вручну через API.
export async function issueClientSubscription(input: {
  user_id: string;
  plan_id: string;
  start_date?: string;
  end_date?: string;
  status?: "ACTIVE" | "FROZEN" | "EXPIRED";
  total_visits?: number | null;
  remaining_visits?: number | null;
}): Promise<Subscription> {
  const data = await request<unknown>("/subscriptions/issue", {
    method: "POST",
    body: JSON.stringify(input)
  });

  return subscriptionSchema.parse(data);
}

// Створює новий план абонемента через API.
export async function createMembershipPlan(
  payload: Omit<MembershipPlan, "id" | "created_at" | "updated_at">
): Promise<MembershipPlan> {
  const data = await request<unknown>("/subscriptions/plans", {
    method: "POST",
    body: JSON.stringify(payload)
  });

  return membershipPlanSchema.parse(data);
}

// Оновлює план абонемента через API.
export async function updateMembershipPlan(
  id: string,
  payload: Partial<Omit<MembershipPlan, "id" | "created_at" | "updated_at">>
): Promise<MembershipPlan> {
  const data = await request<unknown>(`/subscriptions/plans/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });

  return membershipPlanSchema.parse(data);
}

// Видаляє план абонемента через API.
export async function deleteMembershipPlan(id: string): Promise<void> {
  await request<void>(`/subscriptions/plans/${id}`, {
    method: "DELETE"
  });
}

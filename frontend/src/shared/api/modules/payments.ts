// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { Payment } from "../core/contracts";
import { paymentSchema } from "../core/contracts";
import { request } from "../core/http";

// Отримує платежі поточного користувача.
export async function getMyPayments(): Promise<Payment[]> {
  const data = await request<unknown>("/payments/my-payments", { method: "GET" });
  return z.array(paymentSchema).parse(data);
}

// Отримує платежі з фільтрами для адміністративного перегляду.
export async function getPayments(filters?: {
  userId?: string;
  status?: string;
  method?: string;
  startDate?: string;
  endDate?: string;
}): Promise<Payment[]> {
  const params = new URLSearchParams();

  if (filters?.userId) {
    params.set("userId", filters.userId);
  }
  if (filters?.status) {
    params.set("status", filters.status);
  }
  if (filters?.method) {
    params.set("method", filters.method);
  }
  if (filters?.startDate) {
    params.set("startDate", filters.startDate);
  }
  if (filters?.endDate) {
    params.set("endDate", filters.endDate);
  }

  const data = await request<unknown>(`/payments${params.size ? `?${params.toString()}` : ""}`, {
    method: "GET"
  });

  return z.array(paymentSchema).parse(data);
}

// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { ClubStats, MembershipPlan } from "../core/contracts";
import { clubStatsSchema, membershipPlanSchema } from "../core/contracts";
import { request } from "../core/http";

// Отримує публічну статистику клубу для головної сторінки.
export async function getClubStats(): Promise<ClubStats> {
  const data = await request<unknown>("/public/club-stats", { method: "GET" });
  return clubStatsSchema.parse(data);
}

// Отримує список публічних планів абонементів.
export async function getPublicMembershipPlans(): Promise<MembershipPlan[]> {
  const data = await request<unknown>("/public/membership-plans", { method: "GET" });
  return z.array(membershipPlanSchema).parse(data);
}

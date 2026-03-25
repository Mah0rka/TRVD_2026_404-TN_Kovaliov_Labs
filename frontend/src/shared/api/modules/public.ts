// Коротко: модуль виконує API-запити для модуля публічних даних.

import { z } from "zod";

import type { ClubStats, MembershipPlan } from "../core/contracts";
import { clubStatsSchema, membershipPlanSchema } from "../core/contracts";
import { request } from "../core/http";

export async function getClubStats(): Promise<ClubStats> {
  const data = await request<unknown>("/public/club-stats", { method: "GET" });
  return clubStatsSchema.parse(data);
}

export async function getPublicMembershipPlans(): Promise<MembershipPlan[]> {
  const data = await request<unknown>("/public/membership-plans", { method: "GET" });
  return z.array(membershipPlanSchema).parse(data);
}

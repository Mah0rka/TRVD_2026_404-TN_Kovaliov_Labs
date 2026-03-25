// Коротко: модуль виконує API-запити для модуля звітів.

import { z } from "zod";

import type { RevenueReport, TrainerReport } from "../core/contracts";
import { revenueReportSchema, trainerReportSchema } from "../core/contracts";
import { request } from "../core/http";

export async function getRevenueReport(startDate?: string, endDate?: string): Promise<RevenueReport> {
  const params = new URLSearchParams();

  if (startDate) {
    params.set("startDate", startDate);
  }
  if (endDate) {
    params.set("endDate", endDate);
  }

  const data = await request<unknown>(`/reports/revenue${params.size ? `?${params.toString()}` : ""}`, {
    method: "GET"
  });

  return revenueReportSchema.parse(data);
}

export async function getTrainerPopularity(): Promise<TrainerReport[]> {
  const data = await request<unknown>("/reports/trainers/popularity", { method: "GET" });
  return z.array(trainerReportSchema).parse(data);
}

// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { Schedule, ScheduleAttendee } from "../core/contracts";
import { scheduleAttendeeSchema, scheduleSchema } from "../core/contracts";
import { request } from "../core/http";

type ScheduleRecurrenceInput = {
  frequency: "DAILY" | "WEEKLY" | "MONTHLY";
  interval: number;
  byWeekday?: Array<"MO" | "TU" | "WE" | "TH" | "FR" | "SA" | "SU">;
  count?: number | null;
  until?: string | null;
};

function buildRangeQuery(input?: { from?: string; to?: string }): string {
  if (!input?.from && !input?.to) {
    return "";
  }

  const searchParams = new URLSearchParams();
  if (input.from) {
    searchParams.set("from", input.from);
  }
  if (input.to) {
    searchParams.set("to", input.to);
  }
  return `?${searchParams.toString()}`;
}

// Отримує список занять із API.
export async function getSchedules(input?: { from?: string; to?: string }): Promise<Schedule[]> {
  const data = await request<unknown>(`/schedules${buildRangeQuery(input)}`, { method: "GET" });
  return z.array(scheduleSchema).parse(data);
}

// Отримує заняття поточного тренера.
export async function getMyClasses(input?: { from?: string; to?: string }): Promise<Schedule[]> {
  const data = await request<unknown>(`/schedules/my-classes${buildRangeQuery(input)}`, { method: "GET" });
  return z.array(scheduleSchema).parse(data);
}

// Отримує список учасників вибраного заняття.
export async function getScheduleAttendees(classId: string): Promise<ScheduleAttendee[]> {
  const data = await request<unknown>(`/schedules/${classId}/attendees`, { method: "GET" });
  return z.array(scheduleAttendeeSchema).parse(data);
}

// Підтверджує завершення заняття та зберігає коментар.
export async function completeSchedule(
  classId: string,
  input: {
    comment?: string | null;
  }
): Promise<Schedule> {
  const data = await request<unknown>(`/schedules/${classId}/complete`, {
    method: "PATCH",
    body: JSON.stringify(input)
  });
  return scheduleSchema.parse(data);
}

// Створює нове заняття через API.
export async function createSchedule(input: {
  title: string;
  type: "GROUP" | "PERSONAL";
  startTime: string;
  endTime: string;
  capacity: number;
  trainerId?: string;
  isPaidExtra: boolean;
  extraPrice?: number | null;
  recurrence?: ScheduleRecurrenceInput | null;
}): Promise<Schedule> {
  const data = await request<unknown>("/schedules", {
    method: "POST",
    body: JSON.stringify(input)
  });

  return scheduleSchema.parse(data);
}

// Оновлює заняття через API.
export async function updateSchedule(
  id: string,
  input: Partial<{
    title: string;
    type: "GROUP" | "PERSONAL";
    startTime: string;
    endTime: string;
    capacity: number;
    trainerId?: string;
    isPaidExtra: boolean;
    extraPrice?: number | null;
    recurrence?: ScheduleRecurrenceInput | null;
    scope: "OCCURRENCE" | "FOLLOWING" | "SERIES";
  }>
): Promise<Schedule> {
  const data = await request<unknown>(`/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input)
  });

  return scheduleSchema.parse(data);
}

// Видаляє заняття через API.
export async function removeSchedule(
  id: string,
  scope: "OCCURRENCE" | "FOLLOWING" | "SERIES" = "OCCURRENCE"
): Promise<void> {
  const searchParams = new URLSearchParams({ scope });
  await request(`/schedules/${id}?${searchParams.toString()}`, { method: "DELETE" });
}

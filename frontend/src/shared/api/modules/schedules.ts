// Модуль містить виклики API для конкретної предметної області.

import { z } from "zod";

import type { Schedule, ScheduleAttendee } from "../core/contracts";
import { scheduleAttendeeSchema, scheduleSchema } from "../core/contracts";
import { request } from "../core/http";

// Отримує список занять із API.
export async function getSchedules(): Promise<Schedule[]> {
  const data = await request<unknown>("/schedules", { method: "GET" });
  return z.array(scheduleSchema).parse(data);
}

// Отримує заняття поточного тренера.
export async function getMyClasses(): Promise<Schedule[]> {
  const data = await request<unknown>("/schedules/my-classes", { method: "GET" });
  return z.array(scheduleSchema).parse(data);
}

// Отримує список учасників вибраного заняття.
export async function getScheduleAttendees(classId: string): Promise<ScheduleAttendee[]> {
  const data = await request<unknown>(`/schedules/${classId}/attendees`, { method: "GET" });
  return z.array(scheduleAttendeeSchema).parse(data);
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
  }>
): Promise<Schedule> {
  const data = await request<unknown>(`/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input)
  });

  return scheduleSchema.parse(data);
}

// Видаляє заняття через API.
export async function removeSchedule(id: string): Promise<void> {
  await request(`/schedules/${id}`, { method: "DELETE" });
}

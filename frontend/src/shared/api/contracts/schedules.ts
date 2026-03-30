import { z } from "zod";

import {
  recurrenceFrequencySchema,
  recurrenceWeekdaySchema
} from "./common";

export const recurrenceSchema = z.object({
  frequency: recurrenceFrequencySchema,
  interval: z.number(),
  byWeekday: z.array(recurrenceWeekdaySchema).optional().default([]),
  summary: z.string(),
  count: z.number().nullable().optional(),
  until: z.string().nullable().optional()
});

export const scheduleSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  trainer_id: z.string(),
  start_time: z.string(),
  end_time: z.string(),
  capacity: z.number(),
  type: z.enum(["GROUP", "PERSONAL"]),
  is_paid_extra: z.boolean(),
  extra_price: z.coerce.number().nullable(),
  series_id: z.string().nullable().optional(),
  source_occurrence_start: z.string().nullable().optional(),
  is_series_exception: z.boolean().default(false),
  recurrence: recurrenceSchema.nullable().optional(),
  trainer: z.object({
    id: z.string(),
    first_name: z.string(),
    last_name: z.string()
  }),
  completed_at: z.string().nullable().optional(),
  completion_comment: z.string().nullable().optional(),
  completed_by: z
    .object({
      id: z.string(),
      first_name: z.string(),
      last_name: z.string()
    })
    .nullable()
    .optional(),
  bookings: z.array(
    z.object({
      id: z.string(),
      user_id: z.string(),
      status: z.enum(["CONFIRMED", "CANCELLED"])
    })
  ),
  created_at: z.string(),
  updated_at: z.string()
});

export const scheduleAttendeeSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  status: z.enum(["CONFIRMED", "CANCELLED"]),
  created_at: z.string(),
  user: z.object({
    id: z.string(),
    email: z.string().email(),
    first_name: z.string(),
    last_name: z.string()
  })
});

export type Schedule = z.infer<typeof scheduleSchema>;
export type ScheduleAttendee = z.infer<typeof scheduleAttendeeSchema>;
export type ScheduleRecurrence = z.infer<typeof recurrenceSchema>;

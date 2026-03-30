import { z } from "zod";

export const userRoleSchema = z.enum(["CLIENT", "TRAINER", "ADMIN", "OWNER"]);
export const recurrenceScopeSchema = z.enum(["OCCURRENCE", "FOLLOWING", "SERIES"]);
export const recurrenceFrequencySchema = z.enum(["DAILY", "WEEKLY", "MONTHLY"]);
export const recurrenceWeekdaySchema = z.enum(["MO", "TU", "WE", "TH", "FR", "SA", "SU"]);

export type UserRole = z.infer<typeof userRoleSchema>;
export type RecurrenceScope = z.infer<typeof recurrenceScopeSchema>;
export type RecurrenceFrequency = z.infer<typeof recurrenceFrequencySchema>;
export type RecurrenceWeekday = z.infer<typeof recurrenceWeekdaySchema>;

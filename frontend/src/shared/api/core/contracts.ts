// Коротко: ядро API містить базову логіку для контрактів API.

import { z } from "zod";

export const userRoleSchema = z.enum(["CLIENT", "TRAINER", "ADMIN", "OWNER"]);

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  first_name: z.string(),
  last_name: z.string(),
  role: userRoleSchema,
  phone: z.string().nullable(),
  is_verified: z.boolean(),
  created_at: z.string(),
  updated_at: z.string()
});

export const authResponseSchema = z.object({
  user: userSchema
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
  trainer: z.object({
    id: z.string(),
    first_name: z.string(),
    last_name: z.string()
  }),
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

export const subscriptionSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  plan_id: z.string().nullable(),
  type: z.enum(["MONTHLY", "YEARLY", "PAY_AS_YOU_GO"]),
  start_date: z.string(),
  end_date: z.string(),
  status: z.enum(["ACTIVE", "FROZEN", "EXPIRED"]),
  total_visits: z.number().nullable(),
  remaining_visits: z.number().nullable(),
  user: userSchema.nullable().optional(),
  plan: z
    .object({
      id: z.string(),
      title: z.string(),
      description: z.string().nullable(),
      type: z.enum(["MONTHLY", "YEARLY", "PAY_AS_YOU_GO"]),
      duration_days: z.number(),
      visits_limit: z.number().nullable(),
      price: z.coerce.number(),
      currency: z.string(),
      sort_order: z.number(),
      is_active: z.boolean(),
      is_public: z.boolean(),
      created_at: z.string(),
      updated_at: z.string()
    })
    .nullable()
    .optional(),
  last_modified_by: userSchema.nullable().optional(),
  last_modified_at: z.string().nullable().optional(),
  deleted_by: userSchema.nullable().optional(),
  deleted_at: z.string().nullable().optional(),
  restored_by: userSchema.nullable().optional(),
  restored_at: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string()
});

export const membershipPlanSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  type: z.enum(["MONTHLY", "YEARLY", "PAY_AS_YOU_GO"]),
  duration_days: z.number(),
  visits_limit: z.number().nullable(),
  price: z.coerce.number(),
  currency: z.string(),
  sort_order: z.number(),
  is_active: z.boolean(),
  is_public: z.boolean(),
  created_at: z.string(),
  updated_at: z.string()
});

export const bookingSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  class_id: z.string(),
  status: z.enum(["CONFIRMED", "CANCELLED"]),
  created_at: z.string(),
  updated_at: z.string(),
  workout_class: z.object({
    id: z.string(),
    title: z.string(),
    trainer_id: z.string(),
    start_time: z.string(),
    end_time: z.string(),
    capacity: z.number(),
    is_paid_extra: z.boolean(),
    extra_price: z.coerce.number().nullable(),
    trainer: z.object({
      id: z.string(),
      first_name: z.string(),
      last_name: z.string()
    })
  })
});

export const paymentSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  amount: z.coerce.number(),
  currency: z.string(),
  status: z.string(),
  method: z.string(),
  purpose: z.string(),
  description: z.string().nullable().optional(),
  booking_class_id: z.string().nullable().optional(),
  user: userSchema.optional().nullable(),
  created_at: z.string(),
  updated_at: z.string()
});

export const revenueReportSchema = z.object({
  period: z.object({
    startDate: z.string(),
    endDate: z.string()
  }),
  total_revenue: z.number(),
  transactions_count: z.number(),
  currency: z.string()
});

export const trainerReportSchema = z.object({
  trainer_id: z.string(),
  name: z.string(),
  total_attendees: z.number(),
  classes_taught: z.number(),
  average_attendees_per_class: z.number()
});

export const clubStatsSchema = z.object({
  clients_count: z.number(),
  trainers_count: z.number(),
  classes_next_7_days: z.number(),
  active_subscriptions_count: z.number()
});

export type CurrentUser = z.infer<typeof userSchema>;
export type Schedule = z.infer<typeof scheduleSchema>;
export type ScheduleAttendee = z.infer<typeof scheduleAttendeeSchema>;
export type Subscription = z.infer<typeof subscriptionSchema>;
export type MembershipPlan = z.infer<typeof membershipPlanSchema>;
export type Booking = z.infer<typeof bookingSchema>;
export type Payment = z.infer<typeof paymentSchema>;
export type RevenueReport = z.infer<typeof revenueReportSchema>;
export type TrainerReport = z.infer<typeof trainerReportSchema>;
export type ClubStats = z.infer<typeof clubStatsSchema>;
export type UserRole = z.infer<typeof userRoleSchema>;

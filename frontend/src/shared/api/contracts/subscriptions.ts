import { z } from "zod";

import { userSchema } from "./users";

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
  plan: membershipPlanSchema.nullable().optional(),
  last_modified_by: userSchema.nullable().optional(),
  last_modified_at: z.string().nullable().optional(),
  deleted_by: userSchema.nullable().optional(),
  deleted_at: z.string().nullable().optional(),
  restored_by: userSchema.nullable().optional(),
  restored_at: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string()
});

export type MembershipPlan = z.infer<typeof membershipPlanSchema>;
export type Subscription = z.infer<typeof subscriptionSchema>;

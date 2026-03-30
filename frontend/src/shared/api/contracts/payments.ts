import { z } from "zod";

import { userSchema } from "./users";

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

export type Payment = z.infer<typeof paymentSchema>;

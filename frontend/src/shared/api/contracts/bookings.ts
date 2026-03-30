import { z } from "zod";

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

export type Booking = z.infer<typeof bookingSchema>;

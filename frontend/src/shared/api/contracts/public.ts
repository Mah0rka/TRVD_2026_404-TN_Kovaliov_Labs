import { z } from "zod";

export const clubStatsSchema = z.object({
  clients_count: z.number(),
  trainers_count: z.number(),
  classes_next_7_days: z.number(),
  active_subscriptions_count: z.number()
});

export type ClubStats = z.infer<typeof clubStatsSchema>;

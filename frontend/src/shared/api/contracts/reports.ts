import { z } from "zod";

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

export type RevenueReport = z.infer<typeof revenueReportSchema>;
export type TrainerReport = z.infer<typeof trainerReportSchema>;

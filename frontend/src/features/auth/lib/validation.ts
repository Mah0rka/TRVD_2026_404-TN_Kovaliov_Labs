import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Вкажіть коректний email"),
  password: z.string().min(8, "Мінімум 8 символів")
});

export const registerSchema = z.object({
  first_name: z.string().min(2, "Мінімум 2 символи"),
  last_name: z.string().min(2, "Мінімум 2 символи"),
  email: z.string().email("Вкажіть коректний email"),
  password: z.string().min(8, "Мінімум 8 символів")
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;

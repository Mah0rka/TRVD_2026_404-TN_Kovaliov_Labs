import { z } from "zod";

import { userRoleSchema } from "./common";

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

export const paginatedUsersSchema = z.object({
  items: z.array(userSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  total_pages: z.number().int().positive()
});

export type CurrentUser = z.infer<typeof userSchema>;
export type PaginatedUsers = z.infer<typeof paginatedUsersSchema>;

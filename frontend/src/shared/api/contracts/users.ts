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

export type CurrentUser = z.infer<typeof userSchema>;

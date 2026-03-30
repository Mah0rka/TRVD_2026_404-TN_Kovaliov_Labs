import { z } from "zod";

import { userSchema } from "./users";

export const authResponseSchema = z.object({
  user: userSchema
});

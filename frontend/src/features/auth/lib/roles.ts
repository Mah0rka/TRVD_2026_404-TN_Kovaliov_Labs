// Коротко: допоміжний модуль містить утиліти для ролей доступу.

import type { CurrentUser, UserRole } from "../../../shared/api";

type RoleAwareUser = Pick<CurrentUser, "role">;

export const allRoles: UserRole[] = ["CLIENT", "TRAINER", "ADMIN", "OWNER"];
export const clientRoles: UserRole[] = ["CLIENT"];
export const trainerRoles: UserRole[] = ["TRAINER"];
export const managementRoles: UserRole[] = ["ADMIN", "OWNER"];
export const clientAndManagementRoles: UserRole[] = ["CLIENT", "ADMIN", "OWNER"];

export function userHasRole(
  user: RoleAwareUser | null | undefined,
  roles: readonly UserRole[]
): boolean {
  return Boolean(user && roles.includes(user.role));
}

// Модуль містить допоміжну логіку для конкретної фічі.

import type { CurrentUser, UserRole } from "../../../shared/api";

type RoleAwareUser = Pick<CurrentUser, "role">;

export const allRoles: UserRole[] = ["CLIENT", "TRAINER", "ADMIN", "OWNER"];
export const clientRoles: UserRole[] = ["CLIENT"];
export const trainerRoles: UserRole[] = ["TRAINER"];
export const managementRoles: UserRole[] = ["ADMIN", "OWNER"];
export const clientAndManagementRoles: UserRole[] = ["CLIENT", "ADMIN", "OWNER"];
export const trainerAndManagementRoles: UserRole[] = ["TRAINER", "ADMIN", "OWNER"];

// Перевіряє, чи входить роль користувача до дозволеного набору.
export function userHasRole(
  user: RoleAwareUser | null | undefined,
  roles: readonly UserRole[]
): boolean {
  return Boolean(user && roles.includes(user.role));
}

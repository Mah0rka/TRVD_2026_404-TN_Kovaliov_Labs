// Файл містить допоміжну логіку для цього модуля.

import type { UserRole } from "../../shared/api";
import {
  allRoles,
  clientAndManagementRoles,
  clientRoles,
  managementRoles,
  trainerAndManagementRoles
} from "../auth/lib/roles";

export type NavigationItem = {
  to: string;
  label: string;
  roles: readonly UserRole[];
};

export const navigationItems: NavigationItem[] = [
  { to: "/dashboard", label: "Огляд", roles: allRoles },
  { to: "/dashboard/profile", label: "Профіль", roles: allRoles },
  { to: "/dashboard/schedule", label: "Розклад", roles: allRoles },
  { to: "/dashboard/bookings", label: "Мої записи", roles: clientRoles },
  { to: "/dashboard/subscriptions", label: "Абонементи", roles: clientAndManagementRoles },
  { to: "/dashboard/payments", label: "Історія оплат", roles: clientAndManagementRoles },
  { to: "/dashboard/my-classes", label: "Класи", roles: trainerAndManagementRoles },
  { to: "/dashboard/users", label: "Учасники", roles: managementRoles },
  { to: "/dashboard/reports", label: "Аналітика", roles: managementRoles }
];

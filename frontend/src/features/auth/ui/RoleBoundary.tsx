// Компонент інкапсулює частину UI-логіки конкретної фічі.

import { Navigate, Outlet } from "react-router-dom";

import type { UserRole } from "../../../shared/api";
import { userHasRole } from "../lib/roles";
import { useAuthStore } from "../model/store";

// Ховає маршрути й контент від користувачів без потрібної ролі.
export function RoleBoundary({ roles }: { roles: UserRole[] }) {
  const user = useAuthStore((state) => state.user);

  if (!userHasRole(user, roles)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

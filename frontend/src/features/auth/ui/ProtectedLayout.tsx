// Компонент інкапсулює частину UI-логіки конкретної фічі.

import { Navigate, Outlet } from "react-router-dom";

import { AppShell } from "../../../shared/ui/AppShell";
import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

// Не пропускає неавторизованого користувача до захищених маршрутів.
export function ProtectedLayout() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isReady = useAuthStore((state) => state.isReady);

  if (!isReady) {
    return <FullScreenState message="Перевіряємо доступ..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

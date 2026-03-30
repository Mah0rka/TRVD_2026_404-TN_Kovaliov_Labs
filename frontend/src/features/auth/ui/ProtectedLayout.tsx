// ProtectedLayout є єдиною брамою в dashboard-сегмент. Він не знає нічого
// про конкретні ролі чи сторінки нижче, а лише вирішує:
// 1) чи завершився auth bootstrap;
// 2) чи користувач автентифікований;
// 3) у який layout загорнути захищений контент.

import { Navigate, Outlet } from "react-router-dom";

import { DashboardShell } from "../../navigation/ui/DashboardShell";
import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

// DashboardShell підключається саме тут, тому всі дочірні dashboard-роути
// автоматично отримують спільну навігацію та робочу область.
export function ProtectedLayout() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isReady = useAuthStore((state) => state.isReady);

  // Поки AuthBootstrap не виставив isReady, ми не маємо права робити
  // остаточний висновок про доступ користувача.
  if (!isReady) {
    return <FullScreenState message="Перевіряємо доступ..." />;
  }

  // Редірект спрацьовує лише після bootstrap, інакше при hard refresh
  // ми відправили б користувача на /login ще до відновлення сесії.
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <DashboardShell>
      <Outlet />
    </DashboardShell>
  );
}

// Компонент інкапсулює частину UI-логіки конкретної фічі.

import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

// Блокує публічні сторінки для вже авторизованого користувача.
export function PublicOnlyLayout() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isReady = useAuthStore((state) => state.isReady);

  if (!isReady) {
    return <FullScreenState message="Підготовка..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

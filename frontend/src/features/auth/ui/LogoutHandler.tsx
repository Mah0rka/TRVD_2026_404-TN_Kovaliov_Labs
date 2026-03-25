// Коротко: компонент керує UI-логікою для модуля виходу користувача.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { logout } from "../../../shared/api";
import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

export function LogoutHandler() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const navigate = useNavigate();

  useEffect(() => {
    logout()
      .catch(() => undefined)
      .finally(() => {
        clearAuth();
        navigate("/login", { replace: true });
      });
  }, [clearAuth, navigate]);

  return <FullScreenState message="Завершуємо сесію..." />;
}

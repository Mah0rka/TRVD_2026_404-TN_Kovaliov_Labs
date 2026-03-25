// Компонент інкапсулює частину UI-логіки конкретної фічі.

import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "../../../shared/api";
import { AUTH_EXPIRED_EVENT } from "../../../shared/api/core/http";
import { hasSessionHint } from "../lib/session";
import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

// Відновлює сесію під час старту застосунку та синхронізує auth-стан.
export function AuthBootstrap() {
  const setUser = useAuthStore((state) => state.setUser);
  const setReady = useAuthStore((state) => state.setReady);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    const handleAuthExpired = () => {
      clearAuth();
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, [clearAuth]);

  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    retry: false,
    enabled: hasSessionHint()
  });

  useEffect(() => {
    if (!hasSessionHint()) {
      setReady();
      return;
    }

    if (query.data) {
      setUser(query.data);
      return;
    }

    if (query.isError) {
      clearAuth();
      return;
    }

    if (!query.isLoading) {
      setReady();
    }
  }, [clearAuth, query.data, query.isError, query.isLoading, setReady, setUser]);

  if (query.isLoading) {
    return <FullScreenState message="Відновлюємо сесію..." />;
  }

  return <Outlet />;
}

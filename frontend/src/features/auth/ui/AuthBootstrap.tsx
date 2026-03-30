// AuthBootstrap відповідає за "перший кадр" застосунку:
// - слухає глобальну подію завершення сесії від HTTP-клієнта;
// - пробує відновити користувача, якщо в браузері є session hint;
// - переводить auth-store у стан ready, щоб route guards знали, коли можна
//   приймати рішення про редірект.

import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getCurrentUser, queryKeys } from "../../../shared/api";
import { AUTH_EXPIRED_EVENT } from "../../../shared/api/core/http";
import { hasSessionHint } from "../lib/session";
import { useAuthStore } from "../model/store";
import { FullScreenState } from "./FullScreenState";

// Поки цей компонент не завершив bootstrap, захищені layout-и не повинні
// вирішувати, чи редіректити користувача на login.
export function AuthBootstrap() {
  const setUser = useAuthStore((state) => state.setUser);
  const setReady = useAuthStore((state) => state.setReady);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    // HTTP-клієнт не знає про Zustand напряму, тому комунікація йде через DOM-подію.
    // Це зберігає api/core/http.ts незалежним від React-шару.
    const handleAuthExpired = () => {
      clearAuth();
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, [clearAuth]);

  const query = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: getCurrentUser,
    retry: false,
    // Без session hint немає сенсу робити /auth/me: це лише створить зайвий 401
    // на холодному старті неавторизованого користувача.
    enabled: hasSessionHint()
  });

  useEffect(() => {
    // Якщо cookie-підказки нема, auth bootstrap завершується одразу:
    // користувач неавторизований, але route guards уже можуть працювати.
    if (!hasSessionHint()) {
      setReady();
      return;
    }

    // Успішне /auth/me є єдиним місцем, де ми наповнюємо store актуальним user.
    if (query.data) {
      setUser(query.data);
      return;
    }

    // Помилка відновлення означає, що hint застарів або refresh уже недоступний.
    // clearAuth також виставляє isReady=true, тож UI не зависне в bootstrap-стані.
    if (query.isError) {
      clearAuth();
      return;
    }

    // Якщо запит завершився без даних і без помилки, все одно завершуємо bootstrap,
    // щоб маршрутна система не лишалась у вічному "loading".
    if (!query.isLoading) {
      setReady();
    }
  }, [clearAuth, query.data, query.isError, query.isLoading, setReady, setUser]);

  if (query.isLoading) {
    return <FullScreenState message="Відновлюємо сесію..." />;
  }

  // Дочірні маршрути рендеримо лише після синхронізації auth-store.
  return <Outlet />;
}

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  getMyBookings,
  getMyClasses,
  getMyPayments,
  getRevenueReport,
  getSchedules,
  getSubscriptions,
  queryKeys,
  type CurrentUser
} from "../../../shared/api";
import { buildDashboardViewModel } from "../lib/dashboardViewModel";

// Хук ізолює dashboard від знання про конкретні endpoint-и і query keys.
// Сторінка працює вже з готовою view-model, а не з набором окремих API-відповідей.
export function useDashboardData(user: CurrentUser | null) {
  const role = user?.role;
  const isClient = role === "CLIENT";
  const isTrainer = role === "TRAINER";
  const isManagement = role === "ADMIN" || role === "OWNER";

  // Розклад потрібен усім ролям, тому це базова query для будь-якого dashboard.
  const schedulesQuery = useQuery({
    queryKey: queryKeys.dashboard.schedules(),
    queryFn: () => getSchedules()
  });

  // Решта query вмикаються лише тоді, коли вони реально впливають на dashboard
  // конкретної ролі. Це прибирає зайві HTTP-запити і спрощує reasoning про дані.
  const bookingsQuery = useQuery({
    queryKey: queryKeys.dashboard.bookings(),
    queryFn: getMyBookings,
    enabled: isClient
  });

  const subscriptionsQuery = useQuery({
    queryKey: queryKeys.dashboard.subscriptions(),
    queryFn: getSubscriptions,
    enabled: isClient
  });

  const paymentsQuery = useQuery({
    queryKey: queryKeys.dashboard.payments(),
    queryFn: getMyPayments,
    enabled: isClient
  });

  const myClassesQuery = useQuery({
    queryKey: queryKeys.dashboard.myClasses(),
    queryFn: () => getMyClasses(),
    enabled: isTrainer
  });

  const revenueQuery = useQuery({
    queryKey: queryKeys.dashboard.revenue(),
    queryFn: () => getRevenueReport(),
    enabled: isManagement
  });

  const viewModel = useMemo(
    // Сторінка не повинна знати, як із сирих API-відповідей будуються hero/stat/link блоки.
    // Усі null/empty fallback-и застосовуємо тут, щоб buildDashboardViewModel
    // отримував передбачувану форму даних незалежно від статусу окремих query.
    () =>
      buildDashboardViewModel({
        user,
        schedules: schedulesQuery.data ?? [],
        bookings: bookingsQuery.data ?? [],
        subscriptions: subscriptionsQuery.data ?? [],
        payments: paymentsQuery.data ?? [],
        myClasses: myClassesQuery.data ?? [],
        revenue: revenueQuery.data ?? null
      }),
    [
      bookingsQuery.data,
      myClassesQuery.data,
      paymentsQuery.data,
      revenueQuery.data,
      schedulesQuery.data,
      subscriptionsQuery.data,
      user
    ]
  );

  return {
    role,
    isClient,
    isTrainer,
    isManagement,
    // Для сторінки це головний контракт: одна view-model плюс кілька role flags.
    viewModel
  };
}

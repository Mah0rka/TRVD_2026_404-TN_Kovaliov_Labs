// Query keys живуть окремо від сторінок і hooks, бо це:
// - єдине джерело правди для cache namespace-ів;
// - проста точка для invalidateQueries/refetch;
// - спосіб уникнути "магічних" рядків у feature-коді.
export const queryKeys = {
  auth: {
    root: () => ["auth"] as const,
    me: () => ["auth", "me"] as const
  },
  bookings: {
    root: () => ["bookings"] as const,
    mine: () => ["bookings", "mine"] as const
  },
  classes: {
    root: () => ["classes"] as const,
    all: () => ["classes", "all"] as const,
    mine: () => ["classes", "mine"] as const,
    attendees: (classId?: string | null) => ["classes", "attendees", classId ?? ""] as const
  },
  dashboard: {
    root: () => ["dashboard"] as const,
    schedules: () => ["dashboard", "schedules"] as const,
    bookings: () => ["dashboard", "bookings"] as const,
    subscriptions: () => ["dashboard", "subscriptions"] as const,
    payments: () => ["dashboard", "payments"] as const,
    myClasses: () => ["dashboard", "my-classes"] as const,
    revenue: () => ["dashboard", "revenue"] as const
  },
  payments: {
    root: () => ["payments"] as const,
    mine: () => ["payments", "mine"] as const,
    ledger: (userId?: string | null, status?: string | null, method?: string | null) =>
      ["payments", "ledger", userId ?? null, status ?? null, method ?? null] as const
  },
  public: {
    stats: () => ["public", "stats"] as const,
    membershipPlans: () => ["public", "membership-plans"] as const
  },
  reports: {
    revenue: (startDate: string, endDate: string) =>
      ["reports", "revenue", startDate, endDate] as const,
    trainerPopularity: () => ["reports", "trainer-popularity"] as const
  },
  schedules: {
    root: () => ["schedules"] as const,
    all: () => ["schedules"] as const,
    clientList: () => ["schedules", "client-list"] as const,
    calendar: (from: string, to: string) => ["schedules", "calendar", from, to] as const,
    trainers: () => ["schedules", "trainers"] as const,
    attendees: (scheduleId?: string | null) => ["schedules", "attendees", scheduleId ?? ""] as const
  },
  subscriptions: {
    root: () => ["subscriptions"] as const,
    plans: () => ["subscriptions", "plans"] as const,
    mine: () => ["subscriptions", "mine"] as const,
    managedAll: () => ["subscriptions", "managed", "all-users"] as const,
    managedByUser: (userId?: string | null) =>
      ["subscriptions", "managed", "user", userId ?? ""] as const
  },
  users: {
    root: () => ["users"] as const,
    all: () => ["users", "all"] as const,
    list: (role?: string | null) => ["users", "list", role ?? "ALL"] as const
  }
};

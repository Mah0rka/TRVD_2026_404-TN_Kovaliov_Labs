// Тести перевіряють ключові сценарії цього модуля.

import { beforeEach, describe, expect, it, vi } from "vitest";

const requestMock = vi.fn();

vi.mock("../core/http", () => ({
  request: (...args: unknown[]) => requestMock(...args)
}));

import {
  cancelBooking,
  confirmPaidBooking,
  createBooking,
  createPaidBookingCheckout,
  deleteClientSubscription,
  deleteUser,
  createMembershipPlan,
  createSchedule,
  createUser,
  deleteMembershipPlan,
  freezeSubscription,
  getClubStats,
  getCurrentUser,
  getManagedSubscriptions,
  getPublicMembershipPlans,
  getMyBookings,
  getMyClasses,
  getMyPayments,
  getPayments,
  getRevenueReport,
  getScheduleAttendees,
  getSchedules,
  getSubscriptionPlans,
  getSubscriptions,
  getTrainerPopularity,
  getUsers,
  login,
  logout,
  purchaseSubscription,
  restoreClientSubscription,
  register,
  removeSchedule,
  issueClientSubscription,
  updateClientSubscription,
  updateMembershipPlan,
  updateMyProfile,
  updateSchedule,
  updateUser
} from "../index";

const currentUser = {
  id: "user-1",
  email: "user@example.com",
  first_name: "User",
  last_name: "One",
  role: "CLIENT" as const,
  phone: null,
  is_verified: true,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z"
};

const schedule = {
  id: "schedule-1",
  title: "Morning Flow",
  description: null,
  trainer_id: "trainer-1",
  start_time: "2026-03-23T10:00:00Z",
  end_time: "2026-03-23T11:00:00Z",
  capacity: 12,
  type: "GROUP" as const,
  is_paid_extra: false,
  extra_price: null,
  trainer: {
    id: "trainer-1",
    first_name: "Ira",
    last_name: "Coach"
  },
  bookings: [{ id: "booking-1", user_id: "user-1", status: "CONFIRMED" as const }],
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z"
};

const attendee = {
  id: "booking-1",
  user_id: "user-1",
  status: "CONFIRMED" as const,
  created_at: "2026-03-23T00:00:00Z",
  user: {
    id: "user-1",
    email: "user@example.com",
    first_name: "User",
    last_name: "One"
  }
};

const subscription = {
  id: "subscription-1",
  user_id: "user-1",
  plan_id: "plan-1",
  type: "MONTHLY" as const,
  start_date: "2026-03-23T00:00:00Z",
  end_date: "2026-04-23T00:00:00Z",
  status: "ACTIVE" as const,
  total_visits: null,
  remaining_visits: null,
  user: currentUser,
  plan: {
    id: "plan-1",
    title: "Місячний",
    description: "12 занять",
    type: "MONTHLY" as const,
    duration_days: 30,
    visits_limit: 12,
    price: 990,
    currency: "UAH",
    sort_order: 10,
    is_active: true,
    is_public: true,
    created_at: "2026-03-23T00:00:00Z",
    updated_at: "2026-03-23T00:00:00Z"
  },
  last_modified_by: currentUser,
  last_modified_at: "2026-03-23T00:00:00Z",
  deleted_by: null,
  deleted_at: null,
  restored_by: null,
  restored_at: null,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z"
};

const membershipPlan = {
  id: "plan-1",
  title: "Місячний",
  description: "12 занять",
  type: "MONTHLY" as const,
  duration_days: 30,
  visits_limit: 12,
  price: 990,
  currency: "UAH",
  sort_order: 10,
  is_active: true,
  is_public: true,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z"
};

const booking = {
  id: "booking-1",
  user_id: "user-1",
  class_id: "schedule-1",
  status: "CONFIRMED" as const,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z",
  workout_class: {
    id: "schedule-1",
    title: "Morning Flow",
    trainer_id: "trainer-1",
    start_time: "2026-03-23T10:00:00Z",
    end_time: "2026-03-23T11:00:00Z",
    capacity: 12,
    is_paid_extra: false,
    extra_price: null,
    trainer: {
      id: "trainer-1",
      first_name: "Ira",
      last_name: "Coach"
    }
  }
};

const payment = {
  id: "payment-1",
  user_id: "user-1",
  amount: 990,
  currency: "UAH",
  status: "SUCCESS",
  method: "CARD",
  purpose: "SUBSCRIPTION",
  description: "Покупка абонемента: Місячний",
  booking_class_id: null,
  user: currentUser,
  created_at: "2026-03-23T00:00:00Z",
  updated_at: "2026-03-23T00:00:00Z"
};

describe("api modules", () => {
  beforeEach(() => {
    requestMock.mockReset();
  });

  it("handles auth module calls", async () => {
    requestMock.mockResolvedValueOnce({ user: currentUser });
    await expect(login("user@example.com", "Password123!")).resolves.toEqual(currentUser);
    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email: "user@example.com", password: "Password123!" })
      },
      { retryOnAuth: false }
    );

    requestMock.mockResolvedValueOnce({ user: currentUser });
    await register({
      email: "user@example.com",
      password: "Password123!",
      first_name: "User",
      last_name: "One"
    });

    requestMock.mockResolvedValueOnce(currentUser);
    await getCurrentUser();

    requestMock.mockResolvedValueOnce(undefined);
    await logout();
  });

  it("handles users module calls", async () => {
    requestMock.mockResolvedValueOnce(currentUser);
    await updateMyProfile({ first_name: "New" });

    requestMock.mockResolvedValueOnce([currentUser]);
    await getUsers("CLIENT");
    expect(requestMock).toHaveBeenNthCalledWith(2, "/users?role=CLIENT", { method: "GET" });

    requestMock.mockResolvedValueOnce(currentUser);
    await createUser({
      email: "new@example.com",
      password: "Password123!",
      first_name: "New",
      last_name: "User",
      role: "TRAINER"
    });

    requestMock.mockResolvedValueOnce(currentUser);
    await updateUser("user-1", { role: "ADMIN" });

    requestMock.mockResolvedValueOnce(undefined);
    await deleteUser("user-2");
  });

  it("handles schedules module calls", async () => {
    requestMock.mockResolvedValueOnce([schedule]);
    await getSchedules();

    requestMock.mockResolvedValueOnce([schedule]);
    await getMyClasses();

    requestMock.mockResolvedValueOnce([attendee]);
    await getScheduleAttendees("schedule-1");

    requestMock.mockResolvedValueOnce(schedule);
    await createSchedule({
      title: "Morning Flow",
      type: "GROUP",
      startTime: "2026-03-23T10:00:00Z",
      endTime: "2026-03-23T11:00:00Z",
      capacity: 12,
      trainerId: "trainer-1",
      isPaidExtra: false,
      extraPrice: null
    });

    requestMock.mockResolvedValueOnce(schedule);
    await updateSchedule("schedule-1", { title: "Updated" });

    requestMock.mockResolvedValueOnce(undefined);
    await removeSchedule("schedule-1");
  });

  it("handles bookings and subscriptions module calls", async () => {
    requestMock.mockResolvedValueOnce([booking]);
    await getMyBookings();

    requestMock.mockResolvedValueOnce(booking);
    await createBooking("schedule-1");

    requestMock.mockResolvedValueOnce({ ...payment, status: "PENDING", purpose: "BOOKING_EXTRA", booking_class_id: "schedule-1" });
    await createPaidBookingCheckout("schedule-1");

    requestMock.mockResolvedValueOnce(booking);
    await confirmPaidBooking("payment-1");

    requestMock.mockResolvedValueOnce(booking);
    await cancelBooking("booking-1");

    requestMock.mockResolvedValueOnce([subscription]);
    await getSubscriptions();

    requestMock.mockResolvedValueOnce([subscription]);
    await getManagedSubscriptions({ includeDeleted: true });
    expect(requestMock).toHaveBeenNthCalledWith(
      7,
      "/subscriptions?include_deleted=true",
      { method: "GET" }
    );

    requestMock.mockResolvedValueOnce([membershipPlan]);
    await getSubscriptionPlans();

    requestMock.mockResolvedValueOnce(subscription);
    await purchaseSubscription("plan-1");
    expect(requestMock).toHaveBeenNthCalledWith(
      9,
      "/subscriptions/purchase",
      {
        method: "POST",
        body: JSON.stringify({ plan_id: "plan-1" })
      }
    );

    requestMock.mockResolvedValueOnce(subscription);
    await freezeSubscription("subscription-1", 14);

    requestMock.mockResolvedValueOnce(subscription);
    await updateClientSubscription("subscription-1", {
      status: "FROZEN",
      remaining_visits: 5
    });

    requestMock.mockResolvedValueOnce(undefined);
    await deleteClientSubscription("subscription-1");

    requestMock.mockResolvedValueOnce(subscription);
    await restoreClientSubscription("subscription-1");

    requestMock.mockResolvedValueOnce(subscription);
    await issueClientSubscription({
      user_id: "user-1",
      plan_id: "plan-1"
    });

    requestMock.mockResolvedValueOnce(membershipPlan);
    await createMembershipPlan({
      title: "Новий план",
      description: "Опис",
      type: "MONTHLY",
      duration_days: 30,
      visits_limit: 12,
      price: 990,
      currency: "UAH",
      sort_order: 20,
      is_active: true,
      is_public: true
    });

    requestMock.mockResolvedValueOnce(membershipPlan);
    await updateMembershipPlan("plan-1", { title: "Оновлений план" });

    requestMock.mockResolvedValueOnce(undefined);
    await deleteMembershipPlan("plan-1");
  });

  it("handles payments, reports and public module calls", async () => {
    requestMock.mockResolvedValueOnce([payment]);
    await getMyPayments();

    requestMock.mockResolvedValueOnce([payment]);
    await getPayments({
      userId: "user-1",
      status: "SUCCESS",
      method: "CARD",
      startDate: "2026-03-01",
      endDate: "2026-03-31"
    });
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      "/payments?userId=user-1&status=SUCCESS&method=CARD&startDate=2026-03-01&endDate=2026-03-31",
      { method: "GET" }
    );

    requestMock.mockResolvedValueOnce({
      period: { startDate: "2026-03-01", endDate: "2026-03-31" },
      total_revenue: 4500,
      transactions_count: 3,
      currency: "UAH"
    });
    await getRevenueReport("2026-03-01", "2026-03-31");

    requestMock.mockResolvedValueOnce([
      {
        trainer_id: "trainer-1",
        name: "Ira Coach",
        total_attendees: 22,
        classes_taught: 8,
        average_attendees_per_class: 2.75
      }
    ]);
    await getTrainerPopularity();

    requestMock.mockResolvedValueOnce({
      clients_count: 10,
      trainers_count: 2,
      classes_next_7_days: 5,
      active_subscriptions_count: 8
    });
    await getClubStats();

    requestMock.mockResolvedValueOnce([membershipPlan]);
    await getPublicMembershipPlans();
  });
});

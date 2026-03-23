import { beforeEach, describe, expect, it, vi } from "vitest";

const requestMock = vi.fn();

vi.mock("../core/http", () => ({
  request: (...args: unknown[]) => requestMock(...args)
}));

import {
  cancelBooking,
  createBooking,
  createSchedule,
  createUser,
  freezeSubscription,
  getClubStats,
  getCurrentUser,
  getMyBookings,
  getMyClasses,
  getMyPayments,
  getPayments,
  getRevenueReport,
  getScheduleAttendees,
  getSchedules,
  getSubscriptions,
  getTrainerPopularity,
  getUsers,
  login,
  logout,
  purchaseSubscription,
  register,
  removeSchedule,
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
  type: "MONTHLY" as const,
  start_date: "2026-03-23T00:00:00Z",
  end_date: "2026-04-23T00:00:00Z",
  status: "ACTIVE" as const,
  total_visits: null,
  remaining_visits: null,
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
      trainerId: "trainer-1"
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

    requestMock.mockResolvedValueOnce(booking);
    await cancelBooking("booking-1");

    requestMock.mockResolvedValueOnce([subscription]);
    await getSubscriptions();

    requestMock.mockResolvedValueOnce(subscription);
    await purchaseSubscription("YEARLY");

    requestMock.mockResolvedValueOnce(subscription);
    await freezeSubscription("subscription-1", 14);
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
  });
});

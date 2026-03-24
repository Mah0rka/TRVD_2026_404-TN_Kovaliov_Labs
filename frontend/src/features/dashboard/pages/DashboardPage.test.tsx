import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";
import { DashboardPage } from "./DashboardPage";

const getSchedulesMock = vi.fn();
const getMyBookingsMock = vi.fn();
const getSubscriptionsMock = vi.fn();
const getMyPaymentsMock = vi.fn();
const getMyClassesMock = vi.fn();
const getRevenueReportMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getSchedules: () => getSchedulesMock(),
    getMyBookings: () => getMyBookingsMock(),
    getSubscriptions: () => getSubscriptionsMock(),
    getMyPayments: () => getMyPaymentsMock(),
    getMyClasses: () => getMyClassesMock(),
    getRevenueReport: (...args: unknown[]) => getRevenueReportMock(...args)
  };
});

const now = new Date(Date.now() + 60 * 60 * 1000).toISOString();
const later = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();

function makeSchedule(overrides: Record<string, unknown> = {}) {
  return {
    id: "schedule-1",
    title: "Morning Strength",
    description: null,
    trainer_id: "trainer-1",
    start_time: now,
    end_time: later,
    capacity: 12,
    type: "GROUP" as const,
    is_paid_extra: false,
    extra_price: null,
    trainer: {
      id: "trainer-1",
      first_name: "Alex",
      last_name: "Bond"
    },
    bookings: [{ id: "booking-1", user_id: "client-1", status: "CONFIRMED" as const }],
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    getSchedulesMock.mockReset();
    getMyBookingsMock.mockReset();
    getSubscriptionsMock.mockReset();
    getMyPaymentsMock.mockReset();
    getMyClassesMock.mockReset();
    getRevenueReportMock.mockReset();
  });

  it("renders client dashboard summary", async () => {
    useAuthStore.setState({
      user: {
        id: "client-1",
        email: "client@example.com",
        first_name: "Client",
        last_name: "User",
        role: "CLIENT",
        phone: null,
        is_verified: true,
        created_at: now,
        updated_at: now
      },
      isAuthenticated: true,
      isReady: true
    });

    getSchedulesMock.mockResolvedValue([makeSchedule()]);
    getMyBookingsMock.mockResolvedValue([
      {
        id: "booking-1",
        user_id: "client-1",
        class_id: "schedule-1",
        status: "CONFIRMED",
        created_at: now,
        updated_at: now,
        workout_class: {
          id: "schedule-1",
          title: "Morning Strength",
          trainer_id: "trainer-1",
          start_time: now,
          end_time: later,
          capacity: 12,
          is_paid_extra: false,
          extra_price: null,
          trainer: {
            id: "trainer-1",
            first_name: "Alex",
            last_name: "Bond"
          }
        }
      }
    ]);
    getSubscriptionsMock.mockResolvedValue([
      {
        id: "subscription-1",
        user_id: "client-1",
        type: "YEARLY",
        start_date: now,
        end_date: later,
        status: "ACTIVE",
        total_visits: null,
        remaining_visits: null,
        created_at: now,
        updated_at: now
      }
    ]);
    getMyPaymentsMock.mockResolvedValue([
      {
        id: "payment-1",
        user_id: "client-1",
        amount: 1990,
        currency: "UAH",
        status: "SUCCESS",
        method: "CARD",
        created_at: now,
        updated_at: now,
        user: null
      }
    ]);
    getMyClassesMock.mockResolvedValue([]);
    getRevenueReportMock.mockResolvedValue({
      period: { startDate: now, endDate: later },
      total_revenue: 0,
      transactions_count: 0,
      currency: "UAH"
    });

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Твій ритм уже зібраний в одному місці")).toBeInTheDocument();
    expect(await screen.findByText("Абонемент: річний")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Відкрити розклад" })).toHaveAttribute(
      "href",
      "/dashboard/schedule"
    );
    expect(screen.getByRole("heading", { name: "Історія оплат" })).toBeInTheDocument();
  });

  it("renders trainer dashboard summary", async () => {
    useAuthStore.setState({
      user: {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Coach",
        last_name: "User",
        role: "TRAINER",
        phone: null,
        is_verified: true,
        created_at: now,
        updated_at: now
      },
      isAuthenticated: true,
      isReady: true
    });

    getSchedulesMock.mockResolvedValue([makeSchedule()]);
    getMyClassesMock.mockResolvedValue([makeSchedule()]);
    getMyBookingsMock.mockResolvedValue([]);
    getSubscriptionsMock.mockResolvedValue([]);
    getMyPaymentsMock.mockResolvedValue([]);
    getRevenueReportMock.mockResolvedValue({
      period: { startDate: now, endDate: later },
      total_revenue: 0,
      transactions_count: 0,
      currency: "UAH"
    });

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Сьогоднішній графік і команда вже під рукою")).toBeInTheDocument();
    expect(await screen.findByText("Найближчий клас")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Мої класи" })).toHaveAttribute(
      "href",
      "/dashboard/my-classes"
    );
  });

  it("renders management dashboard summary", async () => {
    useAuthStore.setState({
      user: {
        id: "admin-1",
        email: "admin@example.com",
        first_name: "Admin",
        last_name: "User",
        role: "ADMIN",
        phone: null,
        is_verified: true,
        created_at: now,
        updated_at: now
      },
      isAuthenticated: true,
      isReady: true
    });

    getSchedulesMock.mockResolvedValue([makeSchedule()]);
    getMyBookingsMock.mockResolvedValue([]);
    getSubscriptionsMock.mockResolvedValue([]);
    getMyPaymentsMock.mockResolvedValue([]);
    getMyClassesMock.mockResolvedValue([]);
    getRevenueReportMock.mockResolvedValue({
      period: { startDate: now, endDate: later },
      total_revenue: 15500,
      transactions_count: 4,
      currency: "UAH"
    });

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Усе, що потрібно для живого ритму клубу")).toBeInTheDocument();
    expect(await screen.findByText("₴15 500 за 30 днів")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Відкрити аналітику" })).toHaveAttribute(
      "href",
      "/dashboard/reports"
    );
    expect(screen.getByText("Команда і клієнти")).toBeInTheDocument();
  });
});

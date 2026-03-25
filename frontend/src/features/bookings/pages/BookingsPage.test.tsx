// Тести перевіряють ключові сценарії цього модуля.

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../../../test/utils";
import { BookingsPage } from "./BookingsPage";

const getMyBookingsMock = vi.fn();
const cancelBookingMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getMyBookings: () => getMyBookingsMock(),
    cancelBooking: (...args: unknown[]) => cancelBookingMock(...args)
  };
});

describe("BookingsPage", () => {
  beforeEach(() => {
    getMyBookingsMock.mockReset();
    cancelBookingMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders empty state", async () => {
    getMyBookingsMock.mockResolvedValue([]);

    renderWithProviders(<BookingsPage />);

    expect(await screen.findByText("Поки що без активних записів")).toBeInTheDocument();
  });

  it("renders bookings and cancels confirmed one", async () => {
    const user = userEvent.setup();
    const futureStart = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    const futureEnd = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();
    getMyBookingsMock.mockResolvedValue([
      {
        id: "booking-1",
        user_id: "client-1",
        class_id: "class-1",
        status: "CONFIRMED",
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z",
        workout_class: {
          id: "class-1",
          title: "Morning Burn",
          trainer_id: "trainer-1",
          start_time: futureStart,
          end_time: futureEnd,
          capacity: 12,
          is_paid_extra: false,
          extra_price: null,
          trainer: {
            id: "trainer-1",
            first_name: "Ira",
            last_name: "Coach"
          }
        }
      }
    ]);
    cancelBookingMock.mockResolvedValue({ status: "CANCELLED" });

    renderWithProviders(<BookingsPage />);

    expect(await screen.findByText("Morning Burn")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Скасувати" }));

    await waitFor(() => {
      expect(cancelBookingMock).toHaveBeenCalled();
      expect(cancelBookingMock.mock.calls[0]?.[0]).toBe("booking-1");
    });
  });

  it("moves cancelled bookings to history tab instead of active list", async () => {
    const user = userEvent.setup();
    getMyBookingsMock.mockResolvedValue([
      {
        id: "booking-cancelled",
        user_id: "client-1",
        class_id: "class-2",
        status: "CANCELLED",
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z",
        workout_class: {
          id: "class-2",
          title: "Cancelled Flow",
          trainer_id: "trainer-1",
          start_time: "2026-03-26T18:00:00Z",
          end_time: "2026-03-26T19:00:00Z",
          capacity: 1,
          is_paid_extra: true,
          extra_price: 450,
          trainer: {
            id: "trainer-1",
            first_name: "Ira",
            last_name: "Coach"
          }
        }
      }
    ]);

    renderWithProviders(<BookingsPage />);

    expect(await screen.findByText("Поки що без активних записів")).toBeInTheDocument();
    expect(screen.queryByText("Cancelled Flow")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Історія" }));

    expect(await screen.findByText("Cancelled Flow")).toBeInTheDocument();
    expect(screen.getByText("Скасовано")).toBeInTheDocument();
  });

  it("moves finished confirmed bookings to history tab", async () => {
    const user = userEvent.setup();
    const pastStart = new Date(Date.now() - 11 * 60 * 1000).toISOString();
    const pastEnd = new Date(Date.now() - 10 * 60 * 1000).toISOString();
    getMyBookingsMock.mockResolvedValue([
      {
        id: "booking-finished",
        user_id: "client-1",
        class_id: "class-3",
        status: "CONFIRMED",
        created_at: "2026-03-25T17:00:00Z",
        updated_at: "2026-03-25T17:00:00Z",
        workout_class: {
          id: "class-3",
          title: "Finished Session",
          trainer_id: "trainer-1",
          start_time: pastStart,
          end_time: pastEnd,
          capacity: 1,
          is_paid_extra: false,
          extra_price: null,
          trainer: {
            id: "trainer-1",
            first_name: "Ira",
            last_name: "Coach"
          }
        }
      }
    ]);

    renderWithProviders(<BookingsPage />);

    expect(await screen.findByText("Поки що без активних записів")).toBeInTheDocument();
    expect(screen.queryByText("Finished Session")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Історія" }));

    expect(await screen.findByText("Finished Session")).toBeInTheDocument();
    expect(screen.getByText("Підтверджено")).toBeInTheDocument();
  });
});

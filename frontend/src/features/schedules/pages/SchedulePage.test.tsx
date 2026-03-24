import userEvent from "@testing-library/user-event";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";
import { SchedulePage } from "./SchedulePage";

const createBookingMock = vi.fn();
const createScheduleMock = vi.fn();
const getScheduleAttendeesMock = vi.fn();
const getSchedulesMock = vi.fn();
const getUsersMock = vi.fn();
const removeScheduleMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    createBooking: (...args: unknown[]) => createBookingMock(...args),
    createSchedule: (...args: unknown[]) => createScheduleMock(...args),
    getScheduleAttendees: (...args: unknown[]) => getScheduleAttendeesMock(...args),
    getSchedules: () => getSchedulesMock(),
    getUsers: (...args: unknown[]) => getUsersMock(...args),
    removeSchedule: (...args: unknown[]) => removeScheduleMock(...args)
  };
});

const start = new Date(Date.now() + 60 * 60 * 1000).toISOString();
const end = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();

function scheduleFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "schedule-1",
    title: "HIIT",
    description: null,
    trainer_id: "trainer-1",
    start_time: start,
    end_time: end,
    capacity: 10,
    type: "GROUP" as const,
    trainer: { id: "trainer-1", first_name: "Ira", last_name: "Coach" },
    bookings: [{ id: "booking-1", user_id: "client-1", status: "CONFIRMED" as const }],
    created_at: start,
    updated_at: start,
    ...overrides
  };
}

describe("SchedulePage", () => {
  beforeEach(() => {
    createBookingMock.mockReset();
    createScheduleMock.mockReset();
    getScheduleAttendeesMock.mockReset();
    getSchedulesMock.mockReset();
    getUsersMock.mockReset();
    removeScheduleMock.mockReset();
  });

  it("lets client filter and book schedules", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({
      user: {
        id: "client-1",
        email: "client@example.com",
        first_name: "Client",
        last_name: "User",
        role: "CLIENT",
        phone: null,
        is_verified: true,
        created_at: start,
        updated_at: start
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([
      scheduleFixture(),
      scheduleFixture({
        id: "schedule-2",
        title: "Personal Flow",
        type: "PERSONAL",
        bookings: []
      })
    ]);
    createBookingMock.mockResolvedValue({});

    renderWithProviders(<SchedulePage />);

    expect(await screen.findByText("Розклад занять")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "PERSONAL" }));
    expect(screen.getByText("Personal Flow")).toBeInTheDocument();
    expect(screen.queryByText("HIIT")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Усі" }));
    await user.click(screen.getAllByRole("button", { name: "Записатись" })[0]);

    await waitFor(() => {
      expect(createBookingMock.mock.calls[0]?.[0]).toBe("schedule-1");
    });
  });

  it("shows booking error if request fails", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({
      user: {
        id: "client-1",
        email: "client@example.com",
        first_name: "Client",
        last_name: "User",
        role: "CLIENT",
        phone: null,
        is_verified: true,
        created_at: start,
        updated_at: start
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([scheduleFixture()]);
    createBookingMock.mockRejectedValue(new Error("Не вдалося записатися на заняття."));

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "Записатись" }));

    expect(await screen.findByText("Не вдалося записатися на заняття.")).toBeInTheDocument();
  });

  it("lets admin create and remove schedules", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({
      user: {
        id: "admin-1",
        email: "admin@example.com",
        first_name: "Admin",
        last_name: "User",
        role: "ADMIN",
        phone: null,
        is_verified: true,
        created_at: start,
        updated_at: start
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([scheduleFixture()]);
    getUsersMock.mockResolvedValue([
      {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Ira",
        last_name: "Coach",
        role: "TRAINER",
        phone: null,
        is_verified: true,
        created_at: start,
        updated_at: start
      }
    ]);
    createScheduleMock.mockResolvedValue(scheduleFixture());
    removeScheduleMock.mockResolvedValue(undefined);

    renderWithProviders(<SchedulePage />);

    await user.click(screen.getByRole("button", { name: "Додати заняття" }));
    fireEvent.change(screen.getByLabelText("Назва"), { target: { value: "Cycle" } });
    fireEvent.change(screen.getByLabelText("Тип"), { target: { value: "PERSONAL" } });
    fireEvent.change(screen.getByLabelText("Початок"), { target: { value: "2026-03-24T10:00" } });
    fireEvent.change(screen.getByLabelText("Кінець"), { target: { value: "2026-03-24T11:00" } });
    fireEvent.change(screen.getByLabelText("Кількість місць"), { target: { value: "8" } });
    fireEvent.change(screen.getByLabelText("Тренер"), { target: { value: "trainer-1" } });
    await user.click(screen.getByRole("button", { name: "Створити заняття" }));

    await waitFor(() => {
      expect(createScheduleMock).toHaveBeenCalled();
      expect(createScheduleMock.mock.calls[0]?.[0]).toEqual({
        title: "Cycle",
        type: "PERSONAL",
        startTime: "2026-03-24T10:00",
        endTime: "2026-03-24T11:00",
        capacity: 8,
        trainerId: "trainer-1"
      });
    });

    await user.click(screen.getByRole("button", { name: "Видалити" }));
    await waitFor(() => {
      expect(removeScheduleMock.mock.calls[0]?.[0]).toBe("schedule-1");
    });
  });

  it("shows attendees for trainer", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({
      user: {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Trainer",
        last_name: "User",
        role: "TRAINER",
        phone: null,
        is_verified: true,
        created_at: start,
        updated_at: start
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([scheduleFixture()]);
    getScheduleAttendeesMock.mockResolvedValue([
      {
        id: "booking-1",
        user_id: "client-1",
        status: "CONFIRMED",
        created_at: start,
        user: {
          id: "client-1",
          email: "client@example.com",
          first_name: "Client",
          last_name: "User"
        }
      }
    ]);

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "Учасники" }));

    expect(await screen.findByText("Client User")).toBeInTheDocument();
    expect(getScheduleAttendeesMock).toHaveBeenCalledWith("schedule-1");
  });
});

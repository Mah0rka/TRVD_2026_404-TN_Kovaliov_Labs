// Тести перевіряють клієнтський та staff-сценарії сторінки розкладу.

import { forwardRef, useEffect, useImperativeHandle } from "react";
import userEvent from "@testing-library/user-event";
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";
import { SchedulePage } from "./SchedulePage";

const createBookingMock = vi.fn();
const createPaidBookingCheckoutMock = vi.fn();
const confirmPaidBookingMock = vi.fn();
const createScheduleMock = vi.fn();
const getMyPaymentsMock = vi.fn();
const getScheduleAttendeesMock = vi.fn();
const getSchedulesMock = vi.fn();
const getUsersMock = vi.fn();
const removeScheduleMock = vi.fn();
const updateScheduleMock = vi.fn();

vi.mock("@fullcalendar/interaction", () => ({ default: {} }));
vi.mock("@fullcalendar/rrule", () => ({ default: {} }));
vi.mock("@fullcalendar/timegrid", () => ({ default: {} }));
vi.mock("@fullcalendar/core/locales/uk", () => ({ default: {} }));
vi.mock("@fullcalendar/react", () => {
  const MockCalendar = forwardRef(function MockCalendar(props: Record<string, unknown>, ref) {
    useImperativeHandle(ref, () => ({
      getApi: () => ({
        prev: vi.fn(),
        next: vi.fn(),
        today: vi.fn(),
        changeView: vi.fn()
      })
    }));

    useEffect(() => {
      (props.datesSet as ((value: unknown) => void) | undefined)?.({
        start: new Date("2026-03-23T00:00:00Z"),
        end: new Date("2026-03-30T00:00:00Z"),
        view: { title: "23 - 29 березня 2026" }
      });
    }, []);

    return (
      <div data-testid="fullcalendar">
        <button
          type="button"
          onClick={() =>
            (props.select as ((value: unknown) => void) | undefined)?.({
              start: new Date("2026-03-24T10:00:00Z"),
              end: new Date("2026-03-24T11:00:00Z")
            })
          }
        >
          mock-select
        </button>
        {Array.isArray(props.events)
          ? props.events.map((event: Record<string, unknown>) => (
              <button
                key={String(event.id)}
                type="button"
                onClick={() =>
                  (props.eventClick as ((value: unknown) => void) | undefined)?.({
                    event: {
                      extendedProps: event.extendedProps
                    }
                  })
                }
              >
                {String(event.title)}
              </button>
            ))
          : null}
      </div>
    );
  });

  return {
    default: MockCalendar
  };
});

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    createBooking: (...args: unknown[]) => createBookingMock(...args),
    createPaidBookingCheckout: (...args: unknown[]) => createPaidBookingCheckoutMock(...args),
    confirmPaidBooking: (...args: unknown[]) => confirmPaidBookingMock(...args),
    createSchedule: (...args: unknown[]) => createScheduleMock(...args),
    getMyPayments: () => getMyPaymentsMock(),
    getScheduleAttendees: (...args: unknown[]) => getScheduleAttendeesMock(...args),
    getSchedules: (...args: unknown[]) => getSchedulesMock(...args),
    getUsers: (...args: unknown[]) => getUsersMock(...args),
    removeSchedule: (...args: unknown[]) => removeScheduleMock(...args),
    updateSchedule: (...args: unknown[]) => updateScheduleMock(...args)
  };
});

const startDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
startDate.setHours(7, 0, 0, 0);
const endDate = new Date(startDate.getTime() + 60 * 60 * 1000);
const start = startDate.toISOString();
const end = endDate.toISOString();

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
    is_paid_extra: false,
    extra_price: null,
    series_id: null,
    source_occurrence_start: null,
    is_series_exception: false,
    recurrence: null,
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
    createPaidBookingCheckoutMock.mockReset();
    confirmPaidBookingMock.mockReset();
    createScheduleMock.mockReset();
    getMyPaymentsMock.mockReset();
    getScheduleAttendeesMock.mockReset();
    getSchedulesMock.mockReset();
    getUsersMock.mockReset();
    removeScheduleMock.mockReset();
    updateScheduleMock.mockReset();
    getMyPaymentsMock.mockResolvedValue([]);
    getScheduleAttendeesMock.mockResolvedValue([]);
  });

  it("keeps the client booking list flow", async () => {
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
      scheduleFixture({
        bookings: [{ id: "booking-other", user_id: "other-user", status: "CONFIRMED" as const }]
      }),
      scheduleFixture({
        id: "schedule-2",
        title: "Personal Flow",
        type: "PERSONAL",
        bookings: []
      })
    ]);
    createBookingMock.mockResolvedValue({});

    renderWithProviders(<SchedulePage />);

    expect(await screen.findByText("Клієнтський список доступних занять і бронювань.")).toBeInTheDocument();
    expect(screen.queryByTestId("fullcalendar")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "PERSONAL" }));
    expect(screen.getByText("Personal Flow")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Усі" }));
    await user.click(screen.getAllByRole("button", { name: "Записатись" })[0]);

    await waitFor(() => {
      expect(createBookingMock.mock.calls[0]?.[0]).toBe("schedule-1");
    });
  });

  it("renders the staff calendar for trainers", async () => {
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

    renderWithProviders(<SchedulePage />);

    expect(await screen.findByText("Календар занять")).toBeInTheDocument();
    expect(await screen.findByTestId("fullcalendar")).toBeInTheDocument();
    expect(screen.queryByText("Клієнтський список доступних занять і бронювань.")).not.toBeInTheDocument();
  });

  it("lets management create a recurring schedule from an empty slot", async () => {
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

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "mock-select" }));
    const dialog = await screen.findByRole("dialog", { name: "Створення заняття" });

    fireEvent.change(within(dialog).getByLabelText("Назва"), { target: { value: "Cycle" } });
    fireEvent.change(within(dialog).getByLabelText("Тренер"), {
      target: { value: "trainer-1" }
    });
    await user.click(within(dialog).getByRole("button", { name: "Разове" }));
    fireEvent.change(within(dialog).getByLabelText("Завершення"), {
      target: { value: "COUNT" }
    });
    fireEvent.change(within(dialog).getByLabelText("Кількість занять"), {
      target: { value: "6" }
    });
    await user.click(within(dialog).getByRole("button", { name: "Створити заняття" }));

    await waitFor(() => {
      expect(createScheduleMock).toHaveBeenCalled();
      expect(createScheduleMock.mock.calls[0]?.[0]).toMatchObject({
        title: "Cycle",
        trainerId: "trainer-1",
        recurrence: {
          frequency: "WEEKLY",
          interval: 1,
          count: 6
        }
      });
    });
  });

  it("blocks creating a class outside club working hours", async () => {
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

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "Додати заняття" }));
    const dialog = await screen.findByRole("dialog", { name: "Створення заняття" });

    fireEvent.change(within(dialog).getByLabelText("Назва"), { target: { value: "Late Class" } });
    fireEvent.change(within(dialog).getByLabelText("Тренер"), {
      target: { value: "trainer-1" }
    });
    fireEvent.change(within(dialog).getByLabelText("Початок"), {
      target: { value: "2026-03-24T21:00" }
    });
    fireEvent.change(within(dialog).getByLabelText("Кінець"), {
      target: { value: "2026-03-24T23:00" }
    });

    expect(
      within(dialog).getByText(
        "Клуб працює з 06:00 до 22:00, тому заняття має повністю вкладатися в цей інтервал."
      )
    ).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Створити заняття" })).toBeDisabled();
    expect(createScheduleMock).not.toHaveBeenCalled();
  });

  it("prevents trainer from editing another trainer's event", async () => {
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
    getSchedulesMock.mockResolvedValue([
      scheduleFixture({
        title: "Other Coach Session",
        trainer_id: "trainer-2",
        trainer: { id: "trainer-2", first_name: "Other", last_name: "Coach" }
      })
    ]);

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "Увесь клуб" }));
    await user.click(await screen.findByRole("button", { name: "Other Coach Session" }));
    expect(
      await screen.findByText("Це заняття можна переглядати, але не редагувати з цього акаунта.")
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Зберегти зміни" })).not.toBeInTheDocument();
  });

  it("sends the chosen scope when updating a recurring event", async () => {
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
    getSchedulesMock.mockResolvedValue([
      scheduleFixture({
        title: "Recurring Flow",
        series_id: "series-1",
        recurrence: {
          frequency: "WEEKLY",
          interval: 1,
          byWeekday: ["MO", "WE"],
          summary: "Щотижня",
          count: 8,
          until: null
        }
      })
    ]);
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
    updateScheduleMock.mockResolvedValue(scheduleFixture());

    renderWithProviders(<SchedulePage />);

    await user.click(await screen.findByRole("button", { name: "Recurring Flow" }));
    fireEvent.change(screen.getByLabelText("Застосувати зміни до"), {
      target: { value: "FOLLOWING" }
    });
    fireEvent.change(screen.getByLabelText("Назва"), {
      target: { value: "Recurring Flow Updated" }
    });
    await user.click(screen.getByRole("button", { name: "Зберегти зміни" }));

    await waitFor(() => {
      expect(updateScheduleMock).toHaveBeenCalledWith(
        "schedule-1",
        expect.objectContaining({
          title: "Recurring Flow Updated",
          scope: "FOLLOWING"
        })
      );
    });
  });
});

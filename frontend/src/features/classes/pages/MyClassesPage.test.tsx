// Тести перевіряють ключові сценарії цього модуля.

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";
import { MyClassesPage } from "./MyClassesPage";

const completeScheduleMock = vi.fn();
const getMyClassesMock = vi.fn();
const getSchedulesMock = vi.fn();
const getScheduleAttendeesMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    completeSchedule: (...args: unknown[]) => completeScheduleMock(...args),
    getMyClasses: () => getMyClassesMock(),
    getSchedules: () => getSchedulesMock(),
    getScheduleAttendees: (...args: unknown[]) => getScheduleAttendeesMock(...args)
  };
});

const now = "2026-03-23T10:00:00Z";

function makeClass(overrides: Record<string, unknown> = {}) {
  return {
    id: "class-1",
    title: "Morning Flow",
    description: null,
    trainer_id: "trainer-1",
    start_time: "2026-03-23T10:00:00Z",
    end_time: "2026-03-23T11:00:00Z",
    capacity: 12,
    type: "GROUP" as const,
    is_paid_extra: false,
    extra_price: null,
    trainer: { id: "trainer-1", first_name: "Ira", last_name: "Coach" },
    completed_at: null,
    completion_comment: null,
    completed_by: null,
    bookings: [{ id: "booking-1", user_id: "client-1", status: "CONFIRMED" as const }],
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

describe("MyClassesPage", () => {
  beforeEach(() => {
    completeScheduleMock.mockReset();
    getMyClassesMock.mockReset();
    getSchedulesMock.mockReset();
    getScheduleAttendeesMock.mockReset();
  });

  it("shows empty state without classes", async () => {
    useAuthStore.setState({
      user: {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Trainer",
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
    getMyClassesMock.mockResolvedValue([]);

    renderWithProviders(<MyClassesPage />);

    expect(await screen.findByText("У вас зараз немає актуальних занять.")).toBeInTheDocument();
    expect(screen.getByText("Оберіть заняття зліва, щоб побачити деталі.")).toBeInTheDocument();
  });

  it("shows attendees for selected trainer class", async () => {
    const user = userEvent.setup();
    const startTime = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    const endTime = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();
    useAuthStore.setState({
      user: {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Trainer",
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
    getMyClassesMock.mockResolvedValue([
      makeClass({
        start_time: startTime,
        end_time: endTime
      })
    ]);
    getScheduleAttendeesMock.mockResolvedValue([
      {
        id: "booking-1",
        user_id: "client-1",
        status: "CONFIRMED",
        created_at: now,
        user: {
          id: "client-1",
          email: "client@example.com",
          first_name: "Client",
          last_name: "User"
        }
      }
    ]);

    renderWithProviders(<MyClassesPage />);

    await user.click(await screen.findByRole("button", { name: /Morning Flow/i }));

    expect(await screen.findByText("Client User")).toBeInTheDocument();
    expect(screen.getByText("Підтверджено")).toBeInTheDocument();
    expect(
      screen.getByText(
        `Morning Flow · ${new Date(startTime).toLocaleString("uk-UA")} - ${new Date(endTime).toLocaleString("uk-UA")}`
      )
    ).toBeInTheDocument();
  });

  it("lets trainer confirm completed class with comment", async () => {
    const user = userEvent.setup();
    const endedAt = new Date(Date.now() - 10 * 60 * 1000).toISOString();
    const startedAt = new Date(Date.now() - 70 * 60 * 1000).toISOString();

    useAuthStore.setState({
      user: {
        id: "trainer-1",
        email: "trainer@example.com",
        first_name: "Trainer",
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
    getMyClassesMock.mockResolvedValue([
      makeClass({
        start_time: startedAt,
        end_time: endedAt
      })
    ]);
    getScheduleAttendeesMock.mockResolvedValue([]);
    completeScheduleMock.mockResolvedValue(
      makeClass({
        start_time: startedAt,
        end_time: endedAt,
        completed_at: new Date().toISOString(),
        completion_comment: "Усі вправи виконано.",
        completed_by: { id: "trainer-1", first_name: "Trainer", last_name: "User" }
      })
    );

    renderWithProviders(<MyClassesPage />);

    await user.click(await screen.findByRole("button", { name: "Історія" }));
    await user.type(screen.getByLabelText("Коментар після заняття"), "Усі вправи виконано.");
    await user.click(screen.getByRole("button", { name: "Підтвердити завершення" }));

    await waitFor(() => {
      expect(completeScheduleMock).toHaveBeenCalledWith("class-1", {
        comment: "Усі вправи виконано."
      });
    });
  });

  it("shows history of all classes for owner", async () => {
    const user = userEvent.setup();
    const endedAt = new Date(Date.now() - 10 * 60 * 1000).toISOString();
    const startedAt = new Date(Date.now() - 70 * 60 * 1000).toISOString();

    useAuthStore.setState({
      user: {
        id: "owner-1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "Account",
        role: "OWNER",
        phone: null,
        is_verified: true,
        created_at: now,
        updated_at: now
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([
      makeClass({
        id: "class-owner",
        title: "Club History Session",
        start_time: startedAt,
        end_time: endedAt,
        completed_at: new Date().toISOString(),
        completion_comment: "Заняття відбулося за планом.",
        completed_by: { id: "trainer-1", first_name: "Ira", last_name: "Coach" }
      })
    ]);
    getScheduleAttendeesMock.mockResolvedValue([]);

    renderWithProviders(<MyClassesPage />);

    await user.click(await screen.findByRole("button", { name: "Історія" }));

    expect(await screen.findByText("Club History Session")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Заняття відбулося за планом.")).toBeInTheDocument();
  });

  it("shows pending confirmation filter for owner", async () => {
    const user = userEvent.setup();
    const endedAt = new Date(Date.now() - 10 * 60 * 1000).toISOString();
    const startedAt = new Date(Date.now() - 70 * 60 * 1000).toISOString();

    useAuthStore.setState({
      user: {
        id: "owner-1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "Account",
        role: "OWNER",
        phone: null,
        is_verified: true,
        created_at: now,
        updated_at: now
      },
      isAuthenticated: true,
      isReady: true
    });
    getSchedulesMock.mockResolvedValue([
      makeClass({
        id: "class-pending",
        title: "Pending Session",
        start_time: startedAt,
        end_time: endedAt,
        completed_at: null,
        completion_comment: null,
        completed_by: null
      }),
      makeClass({
        id: "class-history",
        title: "Confirmed Session",
        start_time: startedAt,
        end_time: endedAt,
        completed_at: new Date().toISOString(),
        completion_comment: "Все ок.",
        completed_by: { id: "trainer-1", first_name: "Ira", last_name: "Coach" }
      })
    ]);
    getScheduleAttendeesMock.mockResolvedValue([]);

    renderWithProviders(<MyClassesPage />);

    await user.click(await screen.findByRole("button", { name: "Очікує підтвердження" }));

    expect(await screen.findByText("Pending Session")).toBeInTheDocument();
    expect(screen.queryByText("Confirmed Session")).not.toBeInTheDocument();
    expect(screen.getByText("Потрібне підтвердження")).toBeInTheDocument();
  });
});

import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../../../test/utils";
import { MyClassesPage } from "./MyClassesPage";

const getMyClassesMock = vi.fn();
const getScheduleAttendeesMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getMyClasses: () => getMyClassesMock(),
    getScheduleAttendees: (...args: unknown[]) => getScheduleAttendeesMock(...args)
  };
});

const now = "2026-03-23T10:00:00Z";

describe("MyClassesPage", () => {
  beforeEach(() => {
    getMyClassesMock.mockReset();
    getScheduleAttendeesMock.mockReset();
  });

  it("shows empty state without classes", async () => {
    getMyClassesMock.mockResolvedValue([]);

    renderWithProviders(<MyClassesPage />);

    expect(await screen.findByText("У тренера ще немає призначених занять.")).toBeInTheDocument();
    expect(screen.getByText("Оберіть заняття зліва, щоб побачити список клієнтів.")).toBeInTheDocument();
  });

  it("shows attendees for selected class", async () => {
    const user = userEvent.setup();
    getMyClassesMock.mockResolvedValue([
      {
        id: "class-1",
        title: "Morning Flow",
        description: null,
        trainer_id: "trainer-1",
        start_time: now,
        end_time: "2026-03-23T11:00:00Z",
        capacity: 12,
        type: "GROUP",
        trainer: { id: "trainer-1", first_name: "Ira", last_name: "Coach" },
        bookings: [{ id: "booking-1", user_id: "client-1", status: "CONFIRMED" }],
        created_at: now,
        updated_at: now
      }
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
  });
});

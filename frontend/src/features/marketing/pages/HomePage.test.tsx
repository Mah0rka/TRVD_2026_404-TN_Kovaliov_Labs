import userEvent from "@testing-library/user-event";
import { screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

import { HomePage } from "./HomePage";
import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";

const getClubStatsMock = vi.fn();
const getPublicMembershipPlansMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getClubStats: () => getClubStatsMock(),
    getPublicMembershipPlans: () => getPublicMembershipPlansMock()
  };
});

describe("HomePage", () => {
  beforeEach(() => {
    getClubStatsMock.mockReset();
    getPublicMembershipPlansMock.mockReset();
    getClubStatsMock.mockResolvedValue({
      clients_count: 42,
      trainers_count: 6,
      classes_next_7_days: 18,
      active_subscriptions_count: 31
    });
    getPublicMembershipPlansMock.mockResolvedValue([
      {
        id: "plan-1",
        title: "Старт",
        description: "12 занять",
        type: "MONTHLY",
        duration_days: 30,
        visits_limit: 12,
        price: 990,
        currency: "UAH",
        sort_order: 10,
        is_active: true,
        is_public: true,
        created_at: "2026-03-01T00:00:00Z",
        updated_at: "2026-03-01T00:00:00Z"
      }
    ]);
  });

  it("shows login CTA for guests", async () => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: true });

    renderWithProviders(<HomePage />);

    expect(await screen.findByText("42")).toBeInTheDocument();
    expect(await screen.findByText("Старт")).toBeInTheDocument();
    const primaryLinks = screen.getAllByRole("link", { name: "Записатися на пробне" });
    expect(primaryLinks[0]).toHaveAttribute("href", "/login");
  });

  it("shows greeting and dashboard link for authenticated users", async () => {
    useAuthStore.setState({
      user: {
        id: "user-1",
        email: "client@example.com",
        first_name: "Влад",
        last_name: "Ковальов",
        role: "CLIENT",
        phone: null,
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });

    renderWithProviders(<HomePage />);

    expect(await screen.findByRole("link", { name: /Привіт, Влад/i })).toHaveAttribute(
      "href",
      "/dashboard"
    );
  });

  it("opens and closes mobile marketing navigation drawer", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: true });

    renderWithProviders(<HomePage />);

    await user.click(await screen.findByRole("button", { name: "Відкрити меню" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByRole("link", { name: "Classes" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Закрити меню" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });
});

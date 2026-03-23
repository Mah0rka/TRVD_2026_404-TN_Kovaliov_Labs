import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { HomePage } from "./HomePage";
import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";

const getClubStatsMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getClubStats: () => getClubStatsMock()
  };
});

describe("HomePage", () => {
  beforeEach(() => {
    getClubStatsMock.mockReset();
    getClubStatsMock.mockResolvedValue({
      clients_count: 42,
      trainers_count: 6,
      classes_next_7_days: 18,
      active_subscriptions_count: 31
    });
  });

  it("shows login CTA for guests", async () => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: true });

    renderWithProviders(<HomePage />);

    expect(await screen.findByText("42")).toBeInTheDocument();
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
});

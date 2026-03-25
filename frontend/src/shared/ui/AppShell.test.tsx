// Коротко: тести перевіряють сценарії модуля каркаса застосунку.

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { Routes, Route } from "react-router-dom";
import { vi } from "vitest";

import { useAuthStore } from "../../features/auth";
import { renderWithProviders } from "../../test/utils";
import { AppShell } from "./AppShell";

const logoutMock = vi.fn();

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    logout: () => logoutMock()
  };
});

describe("AppShell", () => {
  beforeEach(() => {
    logoutMock.mockReset();
  });

  it("shows only client navigation for client users", () => {
    useAuthStore.setState({
      user: {
        id: "client-1",
        email: "client@example.com",
        first_name: "Client",
        last_name: "User",
        role: "CLIENT",
        phone: null,
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });

    renderWithProviders(
      <Routes>
        <Route
          path="/dashboard"
          element={
            <AppShell>
              <div>dashboard content</div>
            </AppShell>
          }
        />
      </Routes>,
      { route: "/dashboard" }
    );

    expect(screen.getByRole("link", { name: "Мої записи" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Учасники" })).not.toBeInTheDocument();
    expect(screen.getByText("dashboard content")).toBeInTheDocument();
  });

  it("logs out and clears auth", async () => {
    const user = userEvent.setup();
    logoutMock.mockResolvedValue(undefined);
    useAuthStore.setState({
      user: {
        id: "admin-1",
        email: "admin@example.com",
        first_name: "Admin",
        last_name: "User",
        role: "ADMIN",
        phone: null,
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });

    renderWithProviders(
      <Routes>
        <Route
          path="/dashboard"
          element={
            <AppShell>
              <div>dashboard content</div>
            </AppShell>
          }
        />
      </Routes>,
      { route: "/dashboard" }
    );

    await user.click(screen.getByRole("button", { name: "Вийти" }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  it("highlights only the exact current navigation item", () => {
    useAuthStore.setState({
      user: {
        id: "owner-1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "Account",
        role: "OWNER",
        phone: null,
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });

    const { container } = renderWithProviders(
      <Routes>
        <Route
          path="/dashboard/schedule"
          element={
            <AppShell>
              <div>schedule content</div>
            </AppShell>
          }
        />
      </Routes>,
      { route: "/dashboard/schedule" }
    );

    expect(screen.getByRole("link", { name: "Розклад" })).toHaveClass("active");
    expect(screen.getByRole("link", { name: "Огляд" })).not.toHaveClass("active");
    expect(container.querySelectorAll(".sidebar-nav .nav-link.active")).toHaveLength(1);
  });

  it("opens and closes mobile drawer navigation", async () => {
    const user = userEvent.setup();
    useAuthStore.setState({
      user: {
        id: "owner-1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "Account",
        role: "OWNER",
        phone: null,
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });

    renderWithProviders(
      <Routes>
        <Route
          path="/dashboard"
          element={
            <AppShell>
              <div>dashboard content</div>
            </AppShell>
          }
        />
      </Routes>,
      { route: "/dashboard" }
    );

    await user.click(screen.getByRole("button", { name: "Відкрити меню" }));
    expect(screen.getByRole("dialog", { name: "Навігація кабінету" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Закрити меню" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Навігація кабінету" })).not.toBeInTheDocument();
    });
  });
});

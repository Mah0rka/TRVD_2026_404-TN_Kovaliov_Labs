// Тести перевіряють ключові сценарії цього модуля.

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { useAuthStore } from "../model/store";
import { LogoutHandler } from "./LogoutHandler";

const logoutMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    logout: () => logoutMock()
  };
});

describe("LogoutHandler", () => {
  beforeEach(() => {
    logoutMock.mockReset();
    logoutMock.mockResolvedValue(undefined);
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
  });

  it("clears auth and redirects to login", async () => {
    render(
      <MemoryRouter initialEntries={["/logout"]}>
        <Routes>
          <Route path="/logout" element={<LogoutHandler />} />
          <Route path="/login" element={<div>login screen</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Завершуємо сесію...")).toBeInTheDocument();

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
      expect(screen.getByText("login screen")).toBeInTheDocument();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });
});

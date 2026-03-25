// Коротко: тести перевіряють сценарії модуля відновлення сесії.

import type { ReactNode } from "react";
import { screen, waitFor } from "@testing-library/react";
import { render } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { vi } from "vitest";

import { createTestQueryClient } from "../../../test/utils";
import { useAuthStore } from "../model/store";
import { AuthBootstrap } from "./AuthBootstrap";

const getCurrentUserMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getCurrentUser: () => getCurrentUserMock()
  };
});

describe("AuthBootstrap", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: false });
    getCurrentUserMock.mockReset();
    document.cookie = "fcms_csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
  });

  it("marks auth as ready without request when there is no session hint", async () => {
    const queryClient = createTestQueryClient();

    renderWithProvidersWithQuery(
      queryClient,
      <Routes>
        <Route element={<AuthBootstrap />}>
          <Route path="/" element={<div>public page</div>} />
        </Route>
      </Routes>
    );

    expect(await screen.findByText("public page")).toBeInTheDocument();
    expect(getCurrentUserMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isReady).toBe(true);
  });

  it("restores authenticated user when session cookie exists", async () => {
    document.cookie = "fcms_csrf_token=token-value; path=/";
    getCurrentUserMock.mockResolvedValue({
      id: "user-1",
      email: "client@example.com",
      first_name: "Restored",
      last_name: "User",
      role: "CLIENT",
      phone: null,
      is_verified: true,
      created_at: "2026-03-23T00:00:00Z",
      updated_at: "2026-03-23T00:00:00Z"
    });

    const queryClient = createTestQueryClient();

    renderWithProvidersWithQuery(
      queryClient,
      <Routes>
        <Route element={<AuthBootstrap />}>
          <Route path="/" element={<div>restored page</div>} />
        </Route>
      </Routes>
    );

    expect(await screen.findByText("restored page")).toBeInTheDocument();
    await waitFor(() => {
      expect(useAuthStore.getState().user?.first_name).toBe("Restored");
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });
  });
});

function renderWithProvidersWithQuery(queryClient: ReturnType<typeof createTestQueryClient>, ui: ReactNode) {
  return renderWithProvidersNode(
    <MemoryRouter initialEntries={["/"]}>
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    </MemoryRouter>
  );
}

function renderWithProvidersNode(ui: ReactNode) {
  return render(ui);
}

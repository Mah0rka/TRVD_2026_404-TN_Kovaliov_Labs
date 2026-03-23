import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { useAuthStore } from "../model/store";
import { ProtectedLayout } from "./ProtectedLayout";
import { PublicOnlyLayout } from "./PublicOnlyLayout";
import { RoleBoundary } from "./RoleBoundary";

describe("route guards", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: true });
  });

  it("redirects guests away from protected routes", async () => {
    renderRoutes(
      <Routes>
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<div>secret dashboard</div>} />
        </Route>
        <Route path="/login" element={<div>login page</div>} />
      </Routes>,
      "/dashboard"
    );

    expect(await screen.findByText("login page")).toBeInTheDocument();
  });

  it("redirects authenticated users away from public-only routes", async () => {
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

    renderRoutes(
      <Routes>
        <Route element={<PublicOnlyLayout />}>
          <Route path="/login" element={<div>login page</div>} />
        </Route>
        <Route path="/dashboard" element={<div>dashboard page</div>} />
      </Routes>,
      "/login"
    );

    expect(await screen.findByText("dashboard page")).toBeInTheDocument();
  });

  it("blocks users without required role", async () => {
    useAuthStore.setState({
      user: {
        id: "client-2",
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

    renderRoutes(
      <Routes>
        <Route element={<RoleBoundary roles={["ADMIN"]} />}>
          <Route path="/dashboard/users" element={<div>users page</div>} />
        </Route>
        <Route path="/dashboard" element={<div>dashboard page</div>} />
      </Routes>,
      "/dashboard/users"
    );

    expect(await screen.findByText("dashboard page")).toBeInTheDocument();
  });
});

function renderRoutes(ui: ReactNode, route: string) {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
}

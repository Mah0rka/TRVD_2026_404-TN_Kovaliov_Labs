// Тести перевіряють ключові сценарії цього модуля.

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { LoginPage } from "./LoginPage";
import { useAuthStore } from "../model/store";
import { renderWithProviders } from "../../../test/utils";

const navigateMock = vi.fn();
const loginMock = vi.fn();
const registerMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock
  };
});

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    login: (...args: unknown[]) => loginMock(...args),
    register: (...args: unknown[]) => registerMock(...args)
  };
});

describe("LoginPage", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    loginMock.mockReset();
    registerMock.mockReset();
    useAuthStore.setState({ user: null, isAuthenticated: false, isReady: true });
  });

  it("shows validation errors for empty login submission", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await user.click(screen.getByRole("button", { name: "Увійти" }));

    expect(await screen.findByText("Вкажіть коректний email")).toBeInTheDocument();
    expect(screen.getByText("Мінімум 8 символів")).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it("logs in and redirects to dashboard", async () => {
    const user = userEvent.setup();
    loginMock.mockResolvedValue({
      id: "user-1",
      email: "client@example.com",
      first_name: "Vlad",
      last_name: "Koval",
      role: "CLIENT",
      phone: null,
      is_verified: true,
      created_at: "2026-03-23T00:00:00Z",
      updated_at: "2026-03-23T00:00:00Z"
    });

    renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "client@example.com");
    await user.type(screen.getByLabelText("Пароль"), "Password123!");
    await user.click(screen.getByRole("button", { name: "Увійти" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("client@example.com", "Password123!");
      expect(navigateMock).toHaveBeenCalledWith("/dashboard");
      expect(useAuthStore.getState().user?.first_name).toBe("Vlad");
    });
  });

  it("registers a new user in registration mode", async () => {
    const user = userEvent.setup();
    registerMock.mockResolvedValue({
      id: "user-2",
      email: "new@example.com",
      first_name: "New",
      last_name: "Member",
      role: "CLIENT",
      phone: null,
      is_verified: false,
      created_at: "2026-03-23T00:00:00Z",
      updated_at: "2026-03-23T00:00:00Z"
    });

    renderWithProviders(<LoginPage />);

    await user.click(screen.getByRole("button", { name: "Реєстрація" }));
    await user.type(screen.getByLabelText("Ім'я"), "New");
    await user.type(screen.getByLabelText("Прізвище"), "Member");
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Пароль"), "Password123!");
    await user.click(screen.getByRole("button", { name: "Створити акаунт" }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        first_name: "New",
        last_name: "Member",
        email: "new@example.com",
        password: "Password123!"
      });
      expect(navigateMock).toHaveBeenCalledWith("/dashboard");
    });
  });
});

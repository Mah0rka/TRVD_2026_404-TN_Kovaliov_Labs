import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../../../test/utils";
import { UsersPage } from "./UsersPage";

const createUserMock = vi.fn();
const getUsersMock = vi.fn();
const updateUserMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    createUser: (...args: unknown[]) => createUserMock(...args),
    getUsers: (...args: unknown[]) => getUsersMock(...args),
    updateUser: (...args: unknown[]) => updateUserMock(...args)
  };
});

const currentTime = "2026-03-23T00:00:00Z";

const usersFixture = [
  {
    id: "client-1",
    email: "client@example.com",
    first_name: "Client",
    last_name: "One",
    role: "CLIENT" as const,
    phone: null,
    is_verified: true,
    created_at: currentTime,
    updated_at: currentTime
  },
  {
    id: "trainer-1",
    email: "trainer@example.com",
    first_name: "Trainer",
    last_name: "One",
    role: "TRAINER" as const,
    phone: "+380501112233",
    is_verified: false,
    created_at: currentTime,
    updated_at: currentTime
  }
];

describe("UsersPage", () => {
  beforeEach(() => {
    createUserMock.mockReset();
    getUsersMock.mockReset();
    updateUserMock.mockReset();
  });

  it("renders users and filters by role", async () => {
    const user = userEvent.setup();
    getUsersMock.mockResolvedValue(usersFixture);

    renderWithProviders(<UsersPage />);

    expect(await screen.findByText("Учасники клубу")).toBeInTheDocument();
    expect(await screen.findByText("client@example.com")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Фільтр списку"), "TRAINER");

    await waitFor(() => {
      expect(getUsersMock).toHaveBeenLastCalledWith("TRAINER");
    });
  });

  it("creates a user", async () => {
    const user = userEvent.setup();
    getUsersMock.mockResolvedValue(usersFixture);
    createUserMock.mockResolvedValue(usersFixture[0]);

    renderWithProviders(<UsersPage />);

    await screen.findByText("Створити користувача");
    await user.click(screen.getByRole("button", { name: "Відкрити форму створення" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.clear(screen.getByLabelText("Ім'я"));
    await user.type(screen.getByLabelText("Ім'я"), "New");
    await user.clear(screen.getByLabelText("Прізвище"));
    await user.type(screen.getByLabelText("Прізвище"), "Member");
    await user.type(screen.getByLabelText("Телефон"), "+380991234567");
    await user.selectOptions(screen.getAllByLabelText("Доступ")[0], "TRAINER");
    await user.click(screen.getByRole("button", { name: "Створити" }));

    await waitFor(() => {
      expect(createUserMock).toHaveBeenCalled();
      expect(createUserMock.mock.calls[0]?.[0]).toMatchObject({
        email: "new@example.com",
        password: "Password123!",
        first_name: "New",
        last_name: "Member",
        phone: "+380991234567",
        role: "TRAINER"
      });
    });
  });

  it("keeps only one access field in create form", async () => {
    const user = userEvent.setup();
    getUsersMock.mockResolvedValue(usersFixture);

    renderWithProviders(<UsersPage />);

    await screen.findByText("Створити користувача");
    expect(screen.queryByLabelText("Доступ")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Фільтр списку")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Відкрити форму створення" }));
    expect(screen.getAllByLabelText("Доступ")).toHaveLength(1);
  });

  it("toggles create form visibility", async () => {
    const user = userEvent.setup();
    getUsersMock.mockResolvedValue(usersFixture);

    renderWithProviders(<UsersPage />);

    await screen.findByText("Створити користувача");
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Відкрити форму створення" }));
    expect(screen.getByLabelText("Email")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Сховати форму створення" }));
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  });

  it("edits an existing user", async () => {
    const user = userEvent.setup();
    getUsersMock.mockResolvedValue(usersFixture);
    updateUserMock.mockResolvedValue(usersFixture[1]);

    renderWithProviders(<UsersPage />);

    await user.click((await screen.findAllByRole("button", { name: "Редагувати" }))[0]);
    await user.clear(screen.getByLabelText("Ім'я"));
    await user.type(screen.getByLabelText("Ім'я"), "Updated");
    await user.click(screen.getByRole("button", { name: "Зберегти зміни" }));

    await waitFor(() => {
      expect(updateUserMock).toHaveBeenCalled();
      expect(updateUserMock.mock.calls[0]?.[0]).toBe("client-1");
      expect(updateUserMock.mock.calls[0]?.[1]).toMatchObject({
        first_name: "Updated"
      });
    });
  });
});

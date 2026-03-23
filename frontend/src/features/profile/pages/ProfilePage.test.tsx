import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";
import { ProfilePage } from "./ProfilePage";

const updateMyProfileMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    updateMyProfile: (...args: unknown[]) => updateMyProfileMock(...args)
  };
});

describe("ProfilePage", () => {
  beforeEach(() => {
    updateMyProfileMock.mockReset();
    useAuthStore.setState({
      user: {
        id: "client-1",
        email: "client@example.com",
        first_name: "Vlad",
        last_name: "Kovaliov",
        role: "CLIENT",
        phone: "+380501112233",
        is_verified: true,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      },
      isAuthenticated: true,
      isReady: true
    });
  });

  it("validates short names", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfilePage />);

    const nameInput = screen.getByLabelText("Ім'я");
    await user.clear(nameInput);
    await user.type(nameInput, "A");
    await user.click(screen.getByRole("button", { name: "Зберегти профіль" }));

    expect(await screen.findByText("Мінімум 2 символи")).toBeInTheDocument();
    expect(updateMyProfileMock).not.toHaveBeenCalled();
  });

  it("updates profile and syncs auth store", async () => {
    const user = userEvent.setup();
    updateMyProfileMock.mockResolvedValue({
      ...useAuthStore.getState().user,
      first_name: "Volodymyr",
      phone: "+380991234567"
    });

    renderWithProviders(<ProfilePage />);

    await user.clear(screen.getByLabelText("Ім'я"));
    await user.type(screen.getByLabelText("Ім'я"), "Volodymyr");
    await user.clear(screen.getByLabelText("Телефон"));
    await user.type(screen.getByLabelText("Телефон"), "+380991234567");
    await user.click(screen.getByRole("button", { name: "Зберегти профіль" }));

    await waitFor(() => {
      expect(updateMyProfileMock).toHaveBeenCalled();
      expect(updateMyProfileMock.mock.calls[0]?.[0]).toEqual({
        first_name: "Volodymyr",
        last_name: "Kovaliov",
        phone: "+380991234567"
      });
      expect(useAuthStore.getState().user?.first_name).toBe("Volodymyr");
    });
  });
});

import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { PaymentsPage } from "./PaymentsPage";
import { useAuthStore } from "../../auth";
import { renderWithProviders } from "../../../test/utils";

const getMyPaymentsMock = vi.fn();
const getPaymentsMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getMyPayments: () => getMyPaymentsMock(),
    getPayments: (...args: unknown[]) => getPaymentsMock(...args)
  };
});

describe("PaymentsPage", () => {
  beforeEach(() => {
    getMyPaymentsMock.mockReset();
    getPaymentsMock.mockReset();
  });

  it("shows membership purchase history UI for clients", async () => {
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
    getMyPaymentsMock.mockResolvedValue([
      {
        id: "payment-1",
        user_id: "client-1",
        amount: 990,
        currency: "UAH",
        status: "SUCCESS",
        method: "CARD",
        user: null,
        created_at: "2026-03-23T00:00:00Z",
        updated_at: "2026-03-23T00:00:00Z"
      }
    ]);

    renderWithProviders(<PaymentsPage />);

    expect(await screen.findByText("Абонементи продаються зі сторінки тарифів")).toBeInTheDocument();
    expect(await screen.findByText("UAH 990")).toBeInTheDocument();
    expect(getMyPaymentsMock).toHaveBeenCalled();
  });

  it("shows payment ledger filters for management", async () => {
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
    getPaymentsMock.mockResolvedValue([]);

    renderWithProviders(<PaymentsPage />);

    expect(await screen.findByLabelText("Статус")).toBeInTheDocument();
    expect(screen.getByLabelText("Метод")).toBeInTheDocument();
    expect(getPaymentsMock).toHaveBeenCalled();
  });
});

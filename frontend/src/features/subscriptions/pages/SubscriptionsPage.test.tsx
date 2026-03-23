import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../../../test/utils";
import { SubscriptionsPage } from "./SubscriptionsPage";

const getSubscriptionsMock = vi.fn();
const purchaseSubscriptionMock = vi.fn();
const freezeSubscriptionMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getSubscriptions: () => getSubscriptionsMock(),
    purchaseSubscription: (...args: unknown[]) => purchaseSubscriptionMock(...args),
    freezeSubscription: (...args: unknown[]) => freezeSubscriptionMock(...args)
  };
});

describe("SubscriptionsPage", () => {
  beforeEach(() => {
    getSubscriptionsMock.mockReset();
    purchaseSubscriptionMock.mockReset();
    freezeSubscriptionMock.mockReset();
  });

  it("allows purchasing when there is no active subscription", async () => {
    const user = userEvent.setup();
    getSubscriptionsMock.mockResolvedValue([]);
    purchaseSubscriptionMock.mockResolvedValue({});

    renderWithProviders(<SubscriptionsPage />);

    expect(await screen.findByText("Активних абонементів немає")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: "Купити абонемент" })[0]);

    await waitFor(() => {
      expect(purchaseSubscriptionMock).toHaveBeenCalled();
      expect(purchaseSubscriptionMock.mock.calls[0]?.[0]).toBe("MONTHLY");
    });
  });

  it("shows freeze flow for active subscription", async () => {
    const user = userEvent.setup();
    getSubscriptionsMock.mockResolvedValue([
      {
        id: "subscription-1",
        user_id: "client-1",
        type: "MONTHLY",
        start_date: "2026-03-01T00:00:00Z",
        end_date: "2026-03-31T00:00:00Z",
        status: "ACTIVE",
        total_visits: 12,
        remaining_visits: 5,
        created_at: "2026-03-01T00:00:00Z",
        updated_at: "2026-03-01T00:00:00Z"
      }
    ]);
    freezeSubscriptionMock.mockResolvedValue({});

    renderWithProviders(<SubscriptionsPage />);

    expect(await screen.findByText(/У вас уже є/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Заморозити" }));
    await user.click(screen.getByRole("button", { name: "Підтвердити заморозку" }));

    await waitFor(() => {
      expect(freezeSubscriptionMock).toHaveBeenCalled();
      expect(freezeSubscriptionMock.mock.calls[0]?.[0]).toBe("subscription-1");
      expect(freezeSubscriptionMock.mock.calls[0]?.[1]).toBe(7);
    });
  });
});

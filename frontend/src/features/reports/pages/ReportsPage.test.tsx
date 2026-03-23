import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../../../test/utils";
import { ReportsPage } from "./ReportsPage";

const getRevenueReportMock = vi.fn();
const getTrainerPopularityMock = vi.fn();

vi.mock("../../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api")>("../../../shared/api");
  return {
    ...actual,
    getRevenueReport: (...args: unknown[]) => getRevenueReportMock(...args),
    getTrainerPopularity: () => getTrainerPopularityMock()
  };
});

describe("ReportsPage", () => {
  beforeEach(() => {
    getRevenueReportMock.mockReset();
    getTrainerPopularityMock.mockReset();
  });

  it("renders revenue and trainer popularity", async () => {
    getRevenueReportMock.mockResolvedValue({
      period: { startDate: "2026-02-23", endDate: "2026-03-23" },
      total_revenue: 5000,
      transactions_count: 12,
      currency: "UAH"
    });
    getTrainerPopularityMock.mockResolvedValue([
      {
        trainer_id: "trainer-1",
        name: "Ira Coach",
        total_attendees: 18,
        classes_taught: 6,
        average_attendees_per_class: 3
      }
    ]);

    renderWithProviders(<ReportsPage />);

    expect(
      await screen.findByText((content) => content.includes("UAH") && content.includes("5"))
    ).toBeInTheDocument();
    expect(screen.getByText("Ira Coach")).toBeInTheDocument();
    expect(screen.getByText("Транзакцій")).toBeInTheDocument();
  });
});

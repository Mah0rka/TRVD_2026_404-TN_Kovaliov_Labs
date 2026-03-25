// Тести перевіряють ключові сценарії цього модуля.

import { screen } from "@testing-library/react";

import { AppProviders } from "./AppProviders";
import { renderWithProviders } from "../test/utils";

describe("AppProviders", () => {
  it("renders children", () => {
    renderWithProviders(
      <AppProviders>
        <div>provider child</div>
      </AppProviders>
    );

    expect(screen.getByText("provider child")).toBeInTheDocument();
  });
});

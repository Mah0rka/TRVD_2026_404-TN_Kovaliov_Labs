// Тести перевіряють ключові сценарії цього модуля.

import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { renderWithProviders } from "../test/utils";
import { AppRouter } from "./router";

const routerProviderMock = vi.fn(() => <div>router-provider</div>);

vi.mock("react-router/dom", async () => {
  const actual = await vi.importActual<typeof import("react-router/dom")>("react-router/dom");
  return {
    ...actual,
    RouterProvider: (props: unknown) => routerProviderMock(props)
  };
});

describe("AppRouter", () => {
  it("renders RouterProvider with app router", () => {
    renderWithProviders(<AppRouter />);

    expect(screen.getByText("router-provider")).toBeInTheDocument();
    expect(routerProviderMock).toHaveBeenCalled();
  });
});

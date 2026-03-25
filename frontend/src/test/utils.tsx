// Модуль містить спільні тестові утиліти для фронтенду.

import type { PropsWithChildren, ReactElement } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { render } from "@testing-library/react";

// Створює тестовий QueryClient без повторних спроб запитів.
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false
      },
      mutations: {
        retry: false
      }
    }
  });
}

// Рендерить компонент у тесті з потрібними провайдерами.
export function renderWithProviders(
  ui: ReactElement,
  options?: {
    route?: string;
  }
) {
  const queryClient = createTestQueryClient();

  // Огортає тестовий UI потрібними провайдерами.
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <MemoryRouter initialEntries={[options?.route ?? "/"]}>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </MemoryRouter>
    );
  }

  return render(ui, { wrapper: Wrapper });
}

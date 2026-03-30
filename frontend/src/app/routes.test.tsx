// Тести перевіряють ключові сценарії цього модуля.

import { appRouter } from "./routes";

// Збирає вкладені маршрути для перевірки карти роутів у тесті.
function collectRoutes(route: { children?: unknown[]; lazy?: () => Promise<unknown> }) {
  const current = [route];
  const children = Array.isArray(route.children)
    ? route.children.flatMap((child) => collectRoutes(child as { children?: unknown[]; lazy?: () => Promise<unknown> }))
    : [];

  return current.concat(children);
}

describe("appRouter", () => {
  it("defines top-level routes", () => {
    expect(appRouter).toBeDefined();
    expect(appRouter.routes[0]).toBeDefined();
    expect(appRouter.routes[0]).toHaveProperty("hydrateFallbackElement");
  });

  it("loads every lazy route module", async () => {
    const routes = collectRoutes(appRouter.routes[0] as { children?: unknown[]; lazy?: () => Promise<unknown> });
    const expectedPaths = [
      "/",
      "/login",
      "/dashboard",
      "/dashboard/profile",
      "/dashboard/schedule",
      "/dashboard/bookings",
      "/dashboard/subscriptions",
      "/dashboard/payments",
      "/dashboard/my-classes",
      "/dashboard/reports",
      "/dashboard/users"
    ];

    for (const path of expectedPaths) {
      const route = routes.find(
        (candidate) => "path" in candidate && candidate.path === path
      ) as { lazy?: () => Promise<unknown>; Component?: unknown } | undefined;

      expect(route).toBeDefined();

      if (typeof route?.lazy === "function") {
        const loaded = await route.lazy();
        expect(loaded).toHaveProperty("Component");
      } else {
        expect(route).toHaveProperty("Component");
      }
    }
  });
});

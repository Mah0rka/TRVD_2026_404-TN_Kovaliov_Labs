import { appRouter } from "./routes";

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
  });

  it("loads every lazy route module", async () => {
    const routes = collectRoutes(appRouter.routes[0] as { children?: unknown[]; lazy?: () => Promise<unknown> });
    const lazyRoutes = routes.filter((route) => typeof route.lazy === "function");

    expect(lazyRoutes).toHaveLength(10);

    for (const route of lazyRoutes) {
      const loaded = await route.lazy?.();
      expect(loaded).toHaveProperty("Component");
    }
  });
});

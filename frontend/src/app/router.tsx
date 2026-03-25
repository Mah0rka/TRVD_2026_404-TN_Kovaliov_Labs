// Коротко: модуль керує каркасом застосунку та маршрутизації.

import { RouterProvider } from "react-router-dom";

import { appRouter } from "./routes";

export function AppRouter() {
  return <RouterProvider router={appRouter} />;
}

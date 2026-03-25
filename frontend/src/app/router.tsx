// Модуль збирає каркас клієнтського застосунку і його маршрути.

import { RouterProvider } from "react-router-dom";

import { appRouter } from "./routes";

// Підключає роутер як кореневий компонент застосунку.
export function AppRouter() {
  return <RouterProvider router={appRouter} />;
}

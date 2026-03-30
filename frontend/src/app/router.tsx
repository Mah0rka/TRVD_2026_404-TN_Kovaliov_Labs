// RouterProvider винесений у маленький компонент, щоб:
// - main.tsx не знав про реалізацію роутера;
// - тести могли окремо підміняти/монтувати AppRouter;
// - дерево застосунку читалось як набір великих building blocks.

import { RouterProvider } from "react-router/dom";

import { appRouter } from "./routes";

// Єдина відповідальність цього компонента — під'єднати вже зібрану карту маршрутів.
export function AppRouter() {
  return <RouterProvider router={appRouter} />;
}

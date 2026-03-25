// Модуль збирає каркас клієнтського застосунку і його маршрути.

import { createBrowserRouter } from "react-router-dom";

import {
  AuthBootstrap,
  clientAndManagementRoles,
  clientRoles,
  LogoutHandler,
  managementRoles,
  ProtectedLayout,
  PublicOnlyLayout,
  RoleBoundary,
  trainerAndManagementRoles
} from "../features/auth";

// Ліниво підвантажує головну сторінку застосунку.
async function loadHomePage() {
  const module = await import("../features/marketing/pages/HomePage");
  return { Component: module.HomePage };
}

// Ліниво підвантажує сторінку входу.
async function loadLoginPage() {
  const module = await import("../features/auth/pages/LoginPage");
  return { Component: module.LoginPage };
}

// Ліниво підвантажує сторінку дашборду.
async function loadDashboardPage() {
  const module = await import("../features/dashboard/pages/DashboardPage");
  return { Component: module.DashboardPage };
}

// Ліниво підвантажує сторінку профілю.
async function loadProfilePage() {
  const module = await import("../features/profile/pages/ProfilePage");
  return { Component: module.ProfilePage };
}

// Ліниво підвантажує сторінку розкладу.
async function loadSchedulePage() {
  const module = await import("../features/schedules/pages/SchedulePage");
  return { Component: module.SchedulePage };
}

// Ліниво підвантажує сторінку бронювань.
async function loadBookingsPage() {
  const module = await import("../features/bookings/pages/BookingsPage");
  return { Component: module.BookingsPage };
}

// Ліниво підвантажує сторінку абонементів.
async function loadSubscriptionsPage() {
  const module = await import("../features/subscriptions/pages/SubscriptionsPage");
  return { Component: module.SubscriptionsPage };
}

// Ліниво підвантажує сторінку платежів.
async function loadPaymentsPage() {
  const module = await import("../features/payments/pages/PaymentsPage");
  return { Component: module.PaymentsPage };
}

// Ліниво підвантажує сторінку занять тренера.
async function loadMyClassesPage() {
  const module = await import("../features/classes/pages/MyClassesPage");
  return { Component: module.MyClassesPage };
}

// Ліниво підвантажує сторінку звітів.
async function loadReportsPage() {
  const module = await import("../features/reports/pages/ReportsPage");
  return { Component: module.ReportsPage };
}

// Ліниво підвантажує сторінку керування користувачами.
async function loadUsersPage() {
  const module = await import("../features/users/pages/UsersPage");
  return { Component: module.UsersPage };
}

export const appRouter = createBrowserRouter([
  {
    element: <AuthBootstrap />,
    children: [
      {
        path: "/",
        lazy: loadHomePage
      },
      {
        element: <PublicOnlyLayout />,
        children: [
          {
            path: "/login",
            lazy: loadLoginPage
          }
        ]
      },
      {
        element: <ProtectedLayout />,
        children: [
          {
            path: "/dashboard",
            lazy: loadDashboardPage
          },
          {
            path: "/dashboard/profile",
            lazy: loadProfilePage
          },
          {
            path: "/dashboard/schedule",
            lazy: loadSchedulePage
          },
          {
            element: <RoleBoundary roles={clientRoles} />,
            children: [
              {
                path: "/dashboard/bookings",
                lazy: loadBookingsPage
              }
            ]
          },
          {
            element: <RoleBoundary roles={clientAndManagementRoles} />,
            children: [
              {
                path: "/dashboard/subscriptions",
                lazy: loadSubscriptionsPage
              },
              {
                path: "/dashboard/payments",
                lazy: loadPaymentsPage
              }
            ]
          },
          {
            element: <RoleBoundary roles={trainerAndManagementRoles} />,
            children: [
              {
                path: "/dashboard/my-classes",
                lazy: loadMyClassesPage
              }
            ]
          },
          {
            element: <RoleBoundary roles={managementRoles} />,
            children: [
              {
                path: "/dashboard/reports",
                lazy: loadReportsPage
              },
              {
                path: "/dashboard/users",
                lazy: loadUsersPage
              }
            ]
          },
          {
            path: "/logout",
            element: <LogoutHandler />
          }
        ]
      }
    ]
  }
]);

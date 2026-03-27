// Файл містить допоміжну логіку для цього модуля.

import React from "react";
import ReactDOM from "react-dom/client";

import { AppErrorBoundary } from "./app/AppErrorBoundary";
import { AppProviders } from "./app/AppProviders";
import { AppRouter } from "./app/router";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <AppProviders>
        <AppRouter />
      </AppProviders>
    </AppErrorBoundary>
  </React.StrictMode>
);

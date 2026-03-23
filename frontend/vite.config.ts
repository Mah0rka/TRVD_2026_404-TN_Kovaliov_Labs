import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    watch: {
      usePolling: true,
      interval: 250
    },
    hmr: {
      host: "localhost",
      port: 3000
    },
    proxy: {
      "/auth": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/users": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/schedules": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/bookings": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/subscriptions": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/payments": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/reports": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/public": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
});

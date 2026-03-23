import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = process.env.VITE_PROXY_TARGET || env.VITE_PROXY_TARGET || "http://localhost:8000";

  return {
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
          target: proxyTarget,
          changeOrigin: true
        },
        "/users": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/schedules": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/bookings": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/subscriptions": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/payments": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/reports": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/health": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/public": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  };
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;
const apiTarget = process.env.VITE_API_TARGET || "http://localhost:8001";

export default defineConfig(async () => ({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? { protocol: "ws", host, port: 1421 }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      "/health": { target: apiTarget, changeOrigin: true },
      "/data": { target: apiTarget, changeOrigin: true },
      "/features": { target: apiTarget, changeOrigin: true },
      "/strategy": { target: apiTarget, changeOrigin: true },
      "/risk": { target: apiTarget, changeOrigin: true },
      "/backtest": { target: apiTarget, changeOrigin: true },
      "/audit": { target: apiTarget, changeOrigin: true },
      "/paper": { target: apiTarget, changeOrigin: true },
    },
  },
}));

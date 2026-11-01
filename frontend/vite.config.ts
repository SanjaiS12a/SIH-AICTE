import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const backend = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["recharts"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: backend, changeOrigin: false },
      "/accounts": { target: backend, changeOrigin: false },
      "/admin": { target: backend, changeOrigin: false },
      "/static": { target: backend, changeOrigin: false },
    },
  },
});

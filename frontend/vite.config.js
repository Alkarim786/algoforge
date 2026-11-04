import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // File-change events don't cross Docker Desktop's Windows file mount, so poll for edits.
    // The copied Monaco files never change and are thousands of files, so they aren't polled.
    watch: { usePolling: true, interval: 500, ignored: ["**/public/monaco/**"] },
    proxy: {
      "/api": {
        target: process.env.API_PROXY_TARGET || "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});

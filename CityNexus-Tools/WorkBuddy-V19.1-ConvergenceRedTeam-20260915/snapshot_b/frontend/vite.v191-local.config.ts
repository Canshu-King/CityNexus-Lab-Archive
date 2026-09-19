import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// V19.1 isolated lab config.  Not part of the product build.
export default defineConfig({
  plugins: [react()],
  cacheDir: process.env.TEMP ? `${process.env.TEMP}/v191-vite-cache` : ".vite-cache",
  server: {
    host: "127.0.0.1",
    port: 4203,
    strictPort: true,
    proxy: {
      "/api/v1": { target: "http://127.0.0.1:8050", changeOrigin: false },
    },
  },
});

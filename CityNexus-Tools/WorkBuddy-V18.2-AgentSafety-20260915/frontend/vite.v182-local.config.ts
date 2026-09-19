import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// V18.2 isolated lab config.
// - port 4173 (Codex owns 5173 / 8000)
// - /api/v1 proxied to the isolated backend on 8021 (never 8000)
// - cacheDir pinned to %TEMP% so dep-optimize never deletes inside the
//   authoritative tree (the sandbox 50-file delete quota kills Node otherwise)
export default defineConfig({
  plugins: [react()],
  cacheDir: `${process.env.TEMP || "/tmp"}/v182-vite-cache`,
  server: {
    port: 4173,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8021",
        changeOrigin: true,
      },
    },
  },
});

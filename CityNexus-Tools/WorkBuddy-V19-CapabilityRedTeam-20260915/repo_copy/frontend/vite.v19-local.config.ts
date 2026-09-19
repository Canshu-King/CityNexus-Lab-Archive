import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// V19 red-team local config.  Never touches the main worktree:
//  - cacheDir is redirected to %TEMP% (the only delete-quota-exempt zone)
//  - the dev server port and the API proxy target are isolated from Codex
export default defineConfig({
  plugins: [react()],
  cacheDir: `${process.env.TEMP ?? "."}/v19-vite-cache`,
  build: {
    outDir: "dist-v19",
    emptyOutDir: true,
  },
  server: {
    port: 4193,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8040",
        changeOrigin: false,
      },
    },
  },
});

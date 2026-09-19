import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Temporary local override: keep Vite's cache inside the isolated reference-app
// so we never write into the symlinked main-tree node_modules.
export default defineConfig({
  base: "./",
  plugins: [react()],
  cacheDir: ".vite-local",
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/maplibre-gl")) return "vendor-maplibre";
          if (
            id.includes("node_modules/react/") ||
            id.includes("node_modules/react-dom/") ||
            id.includes("node_modules/scheduler/")
          ) {
            return "vendor-react";
          }
          return undefined;
        },
      },
    },
  },
  server: { port: 4177, strictPort: true },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      filename: "v19-1-sw.js",
      injectRegister: "auto",
      manifest: {
        name: "CityNexus V19.1 Capability Shadow",
        short_name: "V19.1 Shadow",
        display: "standalone",
        theme_color: "#0b5b63",
        background_color: "#eef3f1",
        start_url: "/",
      },
      workbox: {
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: /\/api\/v1\//,
            handler: "NetworkFirst",
            options: { cacheName: "v19-1-shadow-api", networkTimeoutSeconds: 3 },
          },
        ],
      },
    }),
  ],
  server: {
    host: "127.0.0.1",
    port: 4202,
    strictPort: true,
    fs: { allow: [fileURLToPath(new URL("..", import.meta.url))] },
    proxy: { "/api/v1": "http://127.0.0.1:8052" },
  },
  preview: {
    host: "127.0.0.1",
    port: 4202,
    strictPort: true,
    fs: { allow: [fileURLToPath(new URL("..", import.meta.url))] },
    proxy: { "/api/v1": "http://127.0.0.1:8052" },
  },
  build: { outDir: "dist", emptyOutDir: true, manifest: true },
});

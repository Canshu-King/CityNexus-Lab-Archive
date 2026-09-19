// Merge into vite.config.ts after the backend gate passes.
server: {
  proxy: {
    "/api/v1": {
      target: "http://127.0.0.1:8000",
      changeOrigin: false,
    },
  },
},

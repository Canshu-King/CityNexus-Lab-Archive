// Merge into playwright.config.ts. Keep both servers local and deterministic.
webServer: [
  {
    command: "cd ../backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
    url: "http://127.0.0.1:8000/api/v1/health",
    reuseExistingServer: true,
  },
  {
    command: "npm run dev -- --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: true,
  },
],

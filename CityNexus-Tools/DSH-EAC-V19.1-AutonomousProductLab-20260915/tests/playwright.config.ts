import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const workdir = path.resolve(here, "..");
const python = "D:/moodle/CityNexus/.venv/Scripts/python.exe";

export default defineConfig({
  testDir: here,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4202",
    viewport: { width: 1280, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8052`,
      cwd: path.resolve(workdir, "lab", "runtime", "backend"),
      env: {
        ...process.env,
        CITYNEXUS_DATABASE_URL: "sqlite:///./v19_1_shadow.db",
        PYTHONDONTWRITEBYTECODE: "1",
      },
      url: "http://127.0.0.1:8052/api/v1/health",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npx vite --config shadow-app/vite.config.ts",
      cwd: workdir,
      url: "http://127.0.0.1:4202",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});

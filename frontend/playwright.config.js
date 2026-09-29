import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:5178",
    trace: "retain-on-failure",
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: `${process.env.E2E_PYTHON || "../.venv/bin/python"} ../tests/servidor_e2e.py`,
      url: "http://127.0.0.1:8765",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5178",
      url: "http://127.0.0.1:5178",
      env: { VITE_API_URL: "http://127.0.0.1:8765/api/v1" },
      reuseExistingServer: false,
    },
  ],
});

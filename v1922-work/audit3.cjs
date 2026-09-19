const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR STACK:\n" + (e.stack || String(e))));
  await page.addInitScript(() => {
    window.localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222");
  });
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  await browser.close();
})();

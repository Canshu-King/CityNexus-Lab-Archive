const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
(async () => {
  await fetch("http://127.0.0.1:8000/api/v1/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const txt = (await page.locator("body").innerText()).replace(/\n+/g, " | ");
  console.log("TRIPS(", txt.length, "):", txt.slice(0, 1800));
  await page.screenshot({ path: SHOTS + "/70_trips.png", fullPage: true });
  await browser.close();
})();

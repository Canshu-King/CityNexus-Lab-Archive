const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8").match(/"([0-9a-f-]{36})"/)[1];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e.stack || e).slice(0,900)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE:", m.text().slice(0,400)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/live", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(9000);
  const det = await page.locator('[data-testid="error-detail"]').innerText().catch(()=>"<none>");
  console.log("DETAIL:", det.slice(0,700));
  await browser.close();
})();

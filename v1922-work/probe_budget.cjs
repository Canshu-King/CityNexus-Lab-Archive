const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/LAB_PROBE_RESULTS.json","utf8")).journey;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,150)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const n = await page.locator('[data-testid="plan-cmp-card"]').count();
  console.log("cards:", n);
  for (let i=0;i<n;i++){
    const band = await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(()=>"?");
    const card = await page.locator('[data-testid="plan-cmp-card"]').nth(i).innerText().catch(()=>"");
    console.log(i, "band=", band.trim(), "|", card.replace(/\n+/g," | ").slice(0,110));
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_budget.png" });
  await browser.close();
})();

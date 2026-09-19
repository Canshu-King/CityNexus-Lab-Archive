const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8").match(/"([0-9a-f-]{36})"/)[1];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,200)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  console.log("journey", J);
  await page.goto("http://127.0.0.1:5173/v8/live", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(9000);
  for (const sel of ["live-disruption","live-proposal","live-accept","live-message","live-no-proposal","live-handled","live-next"]) {
    console.log(sel, "->", await page.locator(`[data-testid="${sel}"]`).count());
  }
  console.log("BODY:", (await page.locator("body").innerText()).replace(/\n+/g," | ").slice(0,500));
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_live3.png" });
  await browser.close();
})();

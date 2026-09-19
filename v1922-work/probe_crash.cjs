const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("crash", () => console.log("!!! CRASH"));
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,200)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(5000);
  await page.locator('.cn-copilot-edge').click();
  await page.waitForTimeout(1500);
  await page.locator('.cn-copilot-form textarea').fill("附近有什么博物馆");
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  for (let i = 0; i < 25; i++) {
    try { await page.waitForTimeout(3000); } catch (e) { console.log("CRASH at", i, String(e).slice(0,80)); return; }
    const h = await page.locator('.cn-copilot-history').innerText().catch(() => "");
    console.log(i, h.replace(/\n+/g," | ").slice(-140));
  }
  await browser.close();
})();

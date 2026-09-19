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
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE", m.text().slice(0,180)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/live", { waitUntil: "domcontentloaded", timeout: 60000 });
  for (let i=0;i<10;i++){ await page.waitForTimeout(3000); console.log("live",i, (await page.locator("body").innerText()).replace(/\n+/g," | ").slice(0,130)); }
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  for (let i=0;i<10;i++){ await page.waitForTimeout(3000); console.log("agent",i, (await page.locator("body").innerText()).replace(/\n+/g," | ").slice(0,130)); }
  await browser.close();
})();

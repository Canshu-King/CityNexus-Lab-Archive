const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("crash", () => console.log("!!! PAGE CRASHED"));
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,150)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE", m.text().slice(0,150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  await page.locator('.cn-copilot-edge').click();
  await page.waitForTimeout(1500);
  const box = page.locator('.cn-copilot-form textarea');
  console.log("textarea:", await box.count());
  await box.fill("鼓浪屿好玩吗？");
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  console.log("submitted at", new Date().toISOString());
  for (let i = 0; i < 25; i++) {
    try { await page.waitForTimeout(3000); } catch (e) { console.log("CRASH AT WAIT", i, String(e).slice(0,90)); break; }
    const h = await page.locator('.cn-copilot-history').innerText().catch(() => "<err>");
    console.log(i, new Date().toISOString(), h.replace(/\n+/g," | ").slice(0,170));
    if (h.length > 120 && i > 3) break;
  }
  await browser.close();
})();

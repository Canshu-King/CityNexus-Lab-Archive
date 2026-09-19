const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,150)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  await page.locator('.cn-copilot-edge').click();
  await page.waitForTimeout(1200);
  await page.locator('.cn-copilot-form textarea').fill("鼓浪屿好玩吗？");
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(3000);
    const h = await page.locator('.cn-copilot-history').innerText().catch(() => "<err>");
    console.log(i, h.replace(/\n+/g," | ").slice(0,320));
    if (h.includes("候选") || h.includes("candidates") || h.includes("查不到") || h.includes("没有找到")) break;
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_copilot3.png", fullPage: true });
  await browser.close();
})();

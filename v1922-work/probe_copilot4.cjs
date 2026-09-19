const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
const QS = ["附近有什么博物馆", "附近有什么公园", "鼓浪屿好玩吗？", "为什么这样安排？"];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,140)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  await page.locator('.cn-copilot-edge').click();
  await page.waitForTimeout(1200);
  for (const q of QS) {
    await page.locator('.cn-copilot-form textarea').fill(q);
    await page.locator('.cn-copilot-form button[type="submit"]').click();
    let last = "";
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(3000);
      last = await page.locator('.cn-copilot-history').innerText().catch(() => "");
      if (last.length > 60 && i >= 1) break;
    }
    console.log("Q:", q, "=>", last.replace(/\n+/g," | ").slice(-320));
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_copilot4.png", fullPage: true });
  await browser.close();
})();

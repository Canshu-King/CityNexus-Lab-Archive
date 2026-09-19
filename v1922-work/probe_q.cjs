const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/VISIBLE_UI_TRACE.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  await page.locator(".cn-copilot-edge").click().catch(()=>{});
  await page.waitForTimeout(1200);
  await page.locator(".cn-copilot-form textarea").fill("鼓浪屿好玩吗？");
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  for (let i=0;i<16;i++){
    await page.waitForTimeout(3000);
    const b = await page.locator(".cn-copilot-bubble.assistant").count();
    if (b>0){
      const t = await page.locator(".cn-copilot-bubble.assistant").last().innerText();
      if (t.trim().length>25){ console.log("ANSWER:", t.replace(/\n+/g," | ").slice(0,240)); break; }
    }
  }
  await browser.close();
})();

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
  page.on("requestfailed", (r) => console.log("REQFAIL", r.url().slice(0,110), r.failure()?.errorText));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  const box = page.locator('.cn-copilot-form textarea');
  console.log("dock count:", await page.locator('[data-testid="v18-copilot-dock"]').count(), "textarea:", await box.count());
  if (await box.count()) {
    await box.fill("鼓浪屿好玩吗？");
    await page.locator('.cn-copilot-form button[type="submit"]').click();
    console.log("submitted");
    for (let i = 0; i < 30; i++) {
      try { await page.waitForTimeout(2000); } catch (e) { console.log("CRASH AT WAIT", i, String(e).slice(0,90)); break; }
      const h = await page.locator('.cn-copilot-history').innerText().catch(() => "<err>");
      console.log(i, h.replace(/\n+/g," | ").slice(0,150));
      if (h.length > 80 && i > 4) break;
    }
  }
  await browser.close();
})();

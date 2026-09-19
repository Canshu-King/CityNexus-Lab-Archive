const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,120)));
  // No journey id at all: first-time traveller state.
  await page.addInitScript(() => localStorage.clear());
  for (const r of ["/v8/hub", "/v8/agent", "/v8/trips"]) {
    await page.goto("http://127.0.0.1:5173" + r, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(5000);
    const body = (await page.locator("body").innerText()).replace(/\n+/g, " | ");
    console.log("===", r, "len:", body.length);
    console.log("   ", body.slice(0, 260));
    await page.screenshot({ path: `D:/moodle/_v1922_work/o2_evidence/shots/empty${r.replace(/\//g,"_")}.png` });
  }
  await browser.close();
})();

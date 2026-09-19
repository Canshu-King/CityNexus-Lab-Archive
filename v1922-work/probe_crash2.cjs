const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  for (const dpr of [1, 2, 3.5]) {
    const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: dpr, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    let crashed = false;
    page.on("crash", () => { crashed = true; });
    page.on("pageerror", (e) => console.log(`  dpr=${dpr} PAGEERROR`, String(e).slice(0,120)));
    try {
      await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
      for (let i=0;i<8;i++){ await page.waitForTimeout(3000); if (crashed) break; }
      console.log(`dpr=${dpr} crashed=${crashed} chars=${(await page.locator("body").innerText().catch(()=>"")).length}`);
    } catch (e) { console.log(`dpr=${dpr} FAIL`, String(e).slice(0,90)); }
    await ctx.close();
  }
  await browser.close();
})();

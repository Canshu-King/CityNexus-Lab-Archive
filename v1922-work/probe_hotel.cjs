const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 3.5, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const J = process.argv[2];
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
  await page.evaluate((j) => localStorage.setItem("citynexus.v8.journey_id", j), J);
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  console.log("URL:", page.url());
  const tids = await page.evaluate(() => [...new Set([...document.querySelectorAll("[data-testid]")].map(e => e.getAttribute("data-testid")))].filter(t => /hotel|stay|book|tab/i.test(t)));
  console.log("relevant testids:", JSON.stringify(tids));
  const tab = page.locator('[data-testid="trips-tab-stays"], [data-testid="trips-tab-hotels"]').first();
  if (await tab.count()) { await tab.click(); await page.waitForTimeout(6000); }
  console.log("URL2:", page.url());
  const tids2 = await page.evaluate(() => [...new Set([...document.querySelectorAll("[data-testid]")].map(e => e.getAttribute("data-testid")))].filter(t => /hotel|stay|choose|chosen/i.test(t)));
  console.log("after tab:", JSON.stringify(tids2));
  const n = await page.locator('[data-testid="hotel-choose"]').count();
  console.log("hotel-choose count:", n);
  if (n) {
    await page.locator('[data-testid="hotel-choose"]').first().click();
    for (let i=0;i<12;i++){ await page.waitForTimeout(2500);
      const c = await page.locator('[data-testid="hotel-chosen"]').count();
      const body = (await page.locator("body").innerText()).replace(/\s+/g," ");
      if (c) { console.log("CHOSEN at", i, "|", body.slice(0,180)); break; }
      if (i===11) console.log("never chosen | body:", body.slice(0,300));
    }
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/final_v2/probe_hotel.png" });
  await browser.close();
})();

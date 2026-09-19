const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 3.5, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const J = process.argv[2];
  page.on("console", m => { if (m.type()==="error") console.log("CONSOLE_ERR", m.text().slice(0,160)); });
  page.on("pageerror", e => console.log("PAGEERROR", String(e).slice(0,160)));
  page.on("response", async r => {
    if (/stays|select|choose/i.test(r.url()) && r.request().method() !== "GET")
      console.log("REQ", r.request().method(), r.url().replace("http://127.0.0.1:8000/api/v1",""), r.status());
  });
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
  await page.evaluate((j) => localStorage.setItem("citynexus.v8.journey_id", j), J);
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  await page.waitForTimeout(9000);
  console.log("cards:", await page.locator('[data-testid="hotel-card"]').count());
  await page.locator('[data-testid="hotel-choose"]').first().click();
  for (let i=0;i<14;i++){
    await page.waitForTimeout(2500);
    const chosen = await page.locator('[data-testid="hotel-chosen"]').count();
    const err = await page.locator('[data-testid="hotel-error"]').count();
    if (chosen || err) {
      console.log(`i=${i} chosen=${chosen} err=${err}`,
        err ? (await page.locator('[data-testid="hotel-error"]').innerText()).slice(0,200) : "");
      break;
    }
    if (i===13) console.log("timeout: no chosen, no error. btn text:", await page.locator('[data-testid="hotel-choose"]').first().innerText());
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/final_v2/probe_hotel3.png", fullPage: true });
  await browser.close();
})();

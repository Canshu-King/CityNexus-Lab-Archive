const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const EV = "D:/moodle/_v1922_work/o2_evidence";
const J = JSON.parse(fs.readFileSync(EV + "/scenario_degraded.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,140)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  // trips -> bookings tab (the traveller path)
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(4000);
  const body = (await page.locator("body").innerText()).replace(/\s+/g," ");
  console.log("bookings-tab:", body.slice(0,220));
  console.log("  leaks UNKNOWN_REALTIME:", /UNKNOWN_REALTIME/.test(body), "| 受保护 C4:", /受保护 C4|Protected C4/.test(body), "| Journey Memory:", /Journey Memory/.test(body), "| STRUCTURED_JSON:", /STRUCTURED_JSON/.test(body), "| DETERMINISTIC:", /DETERMINISTIC/.test(body));
  // Activity detail cost states
  await page.locator('[data-testid="trips-tab-itinerary"]').click();
  await page.waitForTimeout(2500);
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  console.log("stops:", stops);
  for (let i=0;i<Math.min(stops,4);i++){
    await page.locator('[data-testid="trip-stop"]').nth(i).click();
    await page.waitForTimeout(1800);
    const s = await page.locator('[data-testid="activity-cost"]').getAttribute("data-cost-status").catch(()=>"?");
    const txt = await page.locator('[data-testid="activity-cost"]').innerText().catch(()=>"?");
    const title = await page.locator('[data-testid="activity-title"]').innerText().catch(()=>"?");
    console.log("   cost:", s, "|", txt.trim(), "|", title.slice(0,22));
    await page.locator('[data-testid="activity-back"]').click().catch(()=>{});
    await page.waitForTimeout(1200);
  }
  await page.screenshot({ path: EV + "/shots/hotfix_wallet.png" });
  await browser.close();
})();

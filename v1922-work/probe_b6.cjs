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
  const errs = [];
  page.on("pageerror", (e) => errs.push(String(e).slice(0,140)));
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  // B5 deep links with an active journey
  for (const p of ["/v8/today","/v8/copilot","/v8/bookings","/v8/unknownroute"]) {
    await page.goto("http://127.0.0.1:5173" + p, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const t = (await page.locator("body").innerText()).replace(/\s+/g," ").trim();
    console.log("DEEPLINK", p, "chars=", t.length, "|", t.slice(0,90));
  }
  // B2 Me default
  await page.goto("http://127.0.0.1:5173/v8/me", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const me = (await page.locator('[data-testid="v8-me"]').innerText()).replace(/\s+/g," ");
  console.log("ME-BEFORE-ADVANCED:", me.slice(0,180));
  console.log("  leaks ADVISORY:", /ADVISORY/.test(me), "| 权限边界:", /权限边界/.test(me), "| CN-XIAMEN:", /CN-XIAMEN/.test(me));
  // B4 wallet
  await page.goto("http://127.0.0.1:5173/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const bk = (await page.locator('[data-testid="v8-bookings"]').innerText()).replace(/\s+/g," ");
  console.log("WALLET:", bk.slice(0,180));
  console.log("  leaks UNKNOWN_REALTIME:", /UNKNOWN_REALTIME/.test(bk), "| C4:", /受保护 C4|Protected C4/.test(bk), "| Journey Memory:", /Journey Memory/.test(bk));
  // B4 parse feedback
  await page.locator('[data-testid="bookings-advanced"]').locator("summary").click().catch(()=>{});
  await page.waitForTimeout(600);
  await page.locator('[data-testid="bookings-json-input"]').fill("这是一张火车票，厦门到深圳");
  await page.locator('[data-testid="v8-bookings"] button.v8-primary').first().click().catch(()=>{});
  await page.waitForTimeout(1500);
  console.log("PARSE-ERROR:", (await page.locator('[data-testid="bookings-parse-error"]').innerText().catch(()=>"<none>")).slice(0,110));
  // F: budget advisory
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const adv = await page.locator('[data-testid="budget-advisory"]').innerText().catch(()=>"<none>");
  console.log("ADVISORY:", adv.replace(/\s+/g," ").slice(0,150));
  await page.screenshot({ path: EV + "/shots/hotfix_probe.png" });
  console.log("ERRORS:", errs.length, errs.slice(0,2));
  await browser.close();
})();

const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rc_evidence/shots";
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/rc_evidence/be_chain.json", "utf8"));
const JID = chain.journey_id;
fs.mkdirSync(SHOTS, { recursive: true });
const T = [];
const rec = (route, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route, action, status, result: String(result).slice(0, 150) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C:" + m.text().slice(0, 150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  rec("/v8/trips", "itinerary tab", "200", `stops=${await page.locator('[data-testid="trip-stop"]').count()}`);
  await page.screenshot({ path: SHOTS + "/Y1_itinerary.png", fullPage: true });

  await page.locator('[data-testid="trips-tab-stay"]').click();
  await page.waitForTimeout(9000);
  const cards = await page.locator('[data-testid="hotel-card"]').count();
  const names = [];
  for (const el of await page.locator('[data-testid="hotel-name"]').all()) names.push((await el.innerText()).trim());
  rec("/v8/trips", "stay tab", cards ? "200" : "empty", `hotels=${cards} ${names.slice(0, 3).join(", ")}`);
  await page.screenshot({ path: SHOTS + "/Y2_hotels.png", fullPage: true });

  if (cards) {
    await page.locator('[data-testid="hotel-choose"]').first().click();
    await page.waitForTimeout(6000);
    const chosen = await page.locator('[data-testid="hotel-chosen"]').count();
    rec("/v8/trips", "select hotel", chosen ? "200" : "fail", `chosen=${chosen}`);
    await page.screenshot({ path: SHOTS + "/Y3_hotel_selected.png", fullPage: true });
  }

  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(2500);
  rec("/v8/trips", "bookings tab", "200", `len=${(await page.locator("body").innerText()).length}`);
  await page.screenshot({ path: SHOTS + "/Y4_bookings.png", fullPage: true });

  await page.locator('[data-testid="trips-tab-spend"]').click();
  await page.waitForTimeout(2000);
  rec("/v8/trips", "spend tab", "200", "");
  await page.screenshot({ path: SHOTS + "/Y5_spend.png", fullPage: true });

  fs.writeFileSync("D:/moodle/_v1922_work/rc_evidence/fe_xiamen.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.route.padEnd(12)} ${t.action.padEnd(20)} ${t.status.padEnd(8)} ${t.result}`));
  console.log("ERRORS:", errors.length);
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

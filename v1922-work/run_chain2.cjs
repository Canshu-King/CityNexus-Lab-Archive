const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/o2_evidence/shots";
const JID = fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json", "utf8");
const J = JSON.parse(JID).journey_id;
const T = [];
const rec = (route, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: J, route, action, status, result: String(result).slice(0, 170) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 160)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);

  // plan comparison on Today
  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  rec("/v8/hub", "plan-compare", `${cards} cards`, "");
  await page.screenshot({ path: SHOTS + "/R2_compare.png", fullPage: true });
  if (cards > 0) {
    await page.locator('[data-testid="plan-cmp-choose"]').first().click();
    await page.waitForTimeout(5000);
    const still = await page.locator('[data-testid="plan-comparison"]').count();
    rec("/v8/hub", "choose-plan", still === 0 ? "chosen" : "still-visible", "");
  }

  // itinerary
  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  rec("/v8/trips", "itinerary", `${stops} stops`, "");
  await page.screenshot({ path: SHOTS + "/R2_itinerary.png", fullPage: true });

  // activity detail
  if (stops > 0) {
    await page.locator('[data-testid="trip-stop"]').first().click();
    await page.waitForTimeout(1500);
    const open = await page.locator('[data-testid="activity-detail"]').count() > 0;
    rec("/v8/trips", "activity-detail", open ? "opened" : "NO", "");
    await page.screenshot({ path: SHOTS + "/R2_detail.png", fullPage: true });
    await page.locator('[data-testid="activity-back"]').click().catch(() => {});
    await page.waitForTimeout(800);
  }

  // hotels
  await page.locator('[data-testid="trips-tab-stay"]').click();
  await page.waitForTimeout(9000);
  const hotels = await page.locator('[data-testid="hotel-card"]').count();
  rec("/v8/trips", "hotel-compare", `${hotels} hotels`, "");
  await page.screenshot({ path: SHOTS + "/R2_hotels.png", fullPage: true });
  if (hotels > 0) {
    await page.locator('[data-testid="hotel-choose"]').first().click();
    await page.waitForTimeout(6000);
    const chosen = await page.locator('[data-testid="hotel-chosen"]').count();
    rec("/v8/trips", "choose-hotel", chosen > 0 ? "selected" : "not-selected", "");
  }

  fs.writeFileSync("D:/moodle/_v1922_work/o2_evidence/run_chain2.json",
    JSON.stringify({ journey_id: J, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.route.padEnd(11)} ${t.action.padEnd(18)} ${String(t.status).padEnd(14)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

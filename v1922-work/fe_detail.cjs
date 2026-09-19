const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/sk_evidence/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/fc_evidence/b5_journey.json", "utf8"));
const JID = chain.journey_id;
const T = [];
const rec = (action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route: "/v8/trips", action, status, result: String(result).slice(0, 150) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  rec("itinerary-open", `${stops} stops`, "");
  await page.screenshot({ path: SHOTS + "/D1_itinerary.png", fullPage: true });

  if (stops > 0) {
    await page.locator('[data-testid="trip-stop"]').first().click();
    await page.waitForTimeout(1500);
    const open = await page.locator('[data-testid="activity-detail"]').count() > 0;
    rec("open-detail", open ? "opened" : "NOT-OPEN", "");
    const title = await page.locator('[data-testid="activity-title"]').innerText().catch(() => "");
    const dur = await page.locator('[data-testid="activity-duration"]').innerText().catch(() => "");
    const cost = await page.locator('[data-testid="activity-cost"]').innerText().catch(() => "");
    const hours = await page.locator('[data-testid="activity-hours"]').innerText().catch(() => "");
    const loc = await page.locator('[data-testid="activity-location"]').innerText().catch(() => "");
    rec("detail-fields", `${title} | ${dur} | ${cost} | ${hours} | ${loc}`, "");
    await page.screenshot({ path: SHOTS + "/D2_activity_detail.png", fullPage: true });

    await page.locator('[data-testid="activity-back"]').click();
    await page.waitForTimeout(1200);
    rec("back-to-itinerary", (await page.locator('[data-testid="trip-stop"]').count()) > 0 ? "ok" : "fail", "");
  }

  fs.writeFileSync("D:/moodle/_v1922_work/sk_evidence/fe_detail.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 6) }, null, 1));
  T.forEach((t) => console.log(`${t.action.padEnd(22)} ${String(t.status).padEnd(28)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

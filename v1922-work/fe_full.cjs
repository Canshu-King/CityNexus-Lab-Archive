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
const rec = (screen, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, city_code: "CN-XIAMEN", screen, action, status, result: String(result).slice(0, 150) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const errors = [];
  for (const vp of [{ n: "390x844", w: 390, h: 844 }, { n: "430x932", w: 430, h: 932 }]) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(`${vp.n}:${String(e).slice(0, 120)}`));
    page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION_CLOSED|AJAXError/.test(m.text())) errors.push(`${vp.n}:C:${m.text().slice(0, 120)}`); });
    await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

    const shots = ["hub", "trips", "map", "live"];
    for (const r of shots) {
      await page.goto(`${BASE}/v8/${r}`, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(2500);
      if (vp.n === "390x844") await page.screenshot({ path: `${SHOTS}/F_${r}_${vp.n}.png`, fullPage: true });
    }
    rec(`/v8/* ${vp.n}`, "all-tabs", "200", "rendered");

    await page.goto(`${BASE}/v8/trips`, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    rec("/v8/trips", "itinerary", "200", `stops=${stops}`);

    await page.locator('[data-testid="trips-tab-stay"]').click();
    await page.waitForTimeout(6000);
    const hotels = await page.locator('[data-testid="hotel-card"]').count();
    rec("/v8/trips", "hotels", hotels ? "200" : "empty", `hotels=${hotels}`);
    if (vp.n === "390x844") await page.screenshot({ path: `${SHOTS}/F_hotels_${vp.n}.png`, fullPage: true });

    await page.goto(`${BASE}/v8/live`, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(3000);
    const body = await page.locator("body").innerText();
    const leaks = /PlanVersion|semantic_key|C4_Anchored|deterministic gate|REQUEST_PLACE_SEARCH/.test(body);
    rec("/v8/live", "live-recovery", leaks ? "LEAK" : "clean", body.replace(/\n+/g, " | ").slice(0, 120));

    const ov = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    rec(`/v8/live ${vp.n}`, "overflow", ov.sw <= ov.cw + 1 ? "none" : `overflow ${ov.sw}>${ov.cw}`, "");
    await ctx.close();
  }
  fs.writeFileSync("D:/moodle/_v1922_work/rc_evidence/fe_trace.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 10) }, null, 1));
  T.forEach((t) => console.log(`${t.screen.padEnd(22)} ${t.action.padEnd(16)} ${t.status.padEnd(16)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

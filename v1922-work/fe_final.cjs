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
const rec = (route, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route, action, status, result: String(result).slice(0, 150) });
const BANNED = /PlanVersion|C4_Anchored|semantic_key|authority boundary|Authority boundary|Semantic boundary|NONESEARCH|REQUEST_PLACE_SEARCH/;

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const errors = [];
  for (const vp of [{ n: "390x844", w: 390, h: 844 }, { n: "430x932", w: 430, h: 932 }]) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(`${vp.n}:${String(e).slice(0, 120)}`));
    page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push(`${vp.n}:C:${m.text().slice(0, 120)}`); });
    await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

    for (const r of ["hub", "trips", "map", "agent", "me", "live"]) {
      await page.goto(`${BASE}/v8/${r}`, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(1800);
      const body = await page.locator("body").innerText();
      const leak = BANNED.test(body);
      rec(`/v8/${r} ${vp.n}`, "render", leak ? "LEAK" : "clean", body.replace(/\n+/g, " | ").slice(0, 100));
      if (vp.n === "390x844") await page.screenshot({ path: `${SHOTS}/K_${r}_390.png`, fullPage: true });
    }

    // 活动详情
    await page.goto(`${BASE}/v8/trips`, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    if (stops > 0) {
      await page.locator('[data-testid="trip-stop"]').first().click();
      await page.waitForTimeout(1500);
      const open = await page.locator('[data-testid="activity-detail"]').count() > 0;
      rec(`/v8/trips ${vp.n}`, "activity-detail", open ? "opened" : "fail",
        (await page.locator('[data-testid="activity-title"]').innerText().catch(() => "")));
      if (vp.n === "390x844") await page.screenshot({ path: `${SHOTS}/K_activity_detail_390.png`, fullPage: true });
    }

    const ov = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    rec(`/v8 ${vp.n}`, "overflow", ov.sw <= ov.cw + 1 ? "none" : `overflow`, "");
    await ctx.close();
  }
  fs.writeFileSync("D:/moodle/_v1922_work/sk_evidence/fe_final.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.route.padEnd(24)} ${t.action.padEnd(16)} ${String(t.status).padEnd(8)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

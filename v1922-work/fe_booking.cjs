const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/ob_evidence/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/fc_evidence/b5_journey.json", "utf8"));
const JID = chain.journey_id;
const T = [];
const rec = (action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route: "/v8/trips", action, status, result: String(result).slice(0, 160) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(2000);
  rec("open-bookings-tab", "200", "");

  const manualTab = page.locator('[data-testid="inbox-tab-manual"]');
  rec("manual-tab-present", (await manualTab.count()) > 0 ? "yes" : "NO", "");
  await manualTab.click();
  await page.waitForTimeout(800);
  const formOpen = await page.locator('[data-testid="inbox-manual-form"]').count() > 0;
  rec("manual-form-open", formOpen ? "opened" : "NO", "");
  await page.screenshot({ path: SHOTS + "/B1_manual_form.png", fullPage: true });

  if (formOpen) {
    await page.locator('[data-testid="manual-type"]').selectOption("FLIGHT");
    await page.locator('[data-testid="manual-title"]').fill("厦门航空 MF8102 高崎—首都");
    await page.locator('[data-testid="manual-ref"]').fill("MF8102ABC");
    await page.locator('[data-testid="manual-amount"]').fill("1280");
    await page.locator('[data-testid="manual-submit"]').click();
    await page.waitForTimeout(3000);
    const draft = await page.locator('[data-testid="v10-inbox-draft"]').count() > 0;
    rec("preview-draft", draft ? "shown" : "NOT-SHOWN", "");
    const body = await page.locator("body").innerText();
    rec("preview-content", draft ? "ok" : "missing", body.replace(/\n+/g, " | ").slice(0, 140));
    await page.screenshot({ path: SHOTS + "/B2_manual_preview.png", fullPage: true });
  }

  fs.writeFileSync("D:/moodle/_v1922_work/ob_evidence/fe_booking.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 6) }, null, 1));
  T.forEach((t) => console.log(`${t.action.padEnd(22)} ${String(t.status).padEnd(12)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

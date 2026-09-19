const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const SHOTS = "D:/moodle/_v1922_work/o2_evidence/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const T = [];
let JID = null;
const rec = (route, action, status, result, planId) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route, action, status,
           result: String(result).slice(0, 170), plan_id: planId ?? null });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 160)); });

  // 1-2. open "/" and create a fresh Xiamen trip
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2200);
  rec("/", "open-root", "200", (await page.locator("body").innerText()).slice(0, 80));

  // 3. Step 1
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.waitForTimeout(300);
  const inferred = await page.locator('[data-testid="trial-inferred"]').innerText().catch(() => "");
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
  rec("/", "step1", "filled", inferred);

  // 4. Steps 2 and 3
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(600);
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(600);
  const step3 = await page.locator('[data-testid="trial-step3-body"]').count() > 0;
  rec("/", "step3-review", step3 ? "shown" : "MISSING", "");
  await page.screenshot({ path: SHOTS + "/R1_step3.png", fullPage: true });

  // 5. confirm -> creates the journey
  await page.locator('[data-testid="trial-create"]').click();
  await page.waitForTimeout(7000);
  JID = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
  rec("/", "create-confirmed", JID ? "201" : "NO-JOURNEY-ID", JID || "", null);
  await page.screenshot({ path: SHOTS + "/R1_after_create.png", fullPage: true });

  fs.writeFileSync("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.route.padEnd(10)} ${t.action.padEnd(22)} ${String(t.status).padEnd(14)} ${t.result.slice(0, 70)}`));
  console.log("JID:", JID, "| ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

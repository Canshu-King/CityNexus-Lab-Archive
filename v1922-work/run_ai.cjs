const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const SHOTS = "D:/moodle/_v1922_work/o2_evidence/shots";
const JID = "a47f190a-376a-46c3-ba52-a31342f95c47";
const T = [];
const rec = (route, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route, action, status, result: String(result).slice(0, 170) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 160)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  rec("/v8/hub", "today-after-create", "200", (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 120));
  await page.screenshot({ path: SHOTS + "/R1_today_new.png", fullPage: true });

  // AI planning sheet
  const cta = page.locator('[data-testid="hub-plan-with-ai"]');
  rec("/v8/hub", "ai-cta-present", (await cta.count()) > 0 ? "yes" : "NO", "");
  if ((await cta.count()) > 0) {
    await cta.click();
    await page.waitForTimeout(900);
    const open = await page.locator('[data-testid="plan-ai-sheet"]').count() > 0;
    rec("/v8/hub", "ai-sheet-open", open ? "opened" : "NO", "");
    if (open) {
      await page.locator('[data-testid="plan-ai-input"]').fill("两个人去厦门，想去鼓浪屿、环岛路和中山路，不要太赶，想吃本地美食。");
      await page.locator('[data-testid="plan-ai-submit"]').click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: SHOTS + "/R1_ai_progress.png", fullPage: true });
      await page.waitForTimeout(9000);
      const res = await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "");
      rec("/v8/hub", "ai-result", res ? "shown" : "none", res.split("\n")[0] || "");
      await page.screenshot({ path: SHOTS + "/R1_ai_result.png", fullPage: true });
    }
  }
  fs.writeFileSync("D:/moodle/_v1922_work/o2_evidence/run_ai.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.action.padEnd(22)} ${String(t.status).padEnd(10)} ${t.result}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

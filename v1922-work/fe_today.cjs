const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/ob_evidence/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/fc_evidence/b5_journey.json", "utf8"));
const JID = chain.journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError/.test(m.text())) errors.push("C:" + m.text().slice(0, 150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const out = {
    heading: await page.locator('[data-testid="today-heading"]').innerText().catch(() => ""),
    when: await page.locator('[data-testid="today-when"]').innerText().catch(() => ""),
    next: await page.locator('[data-testid="today-next"]').innerText().catch(() => ""),
    stay: await page.locator('[data-testid="today-stay"]').innerText().catch(() => ""),
    attention: await page.locator('[data-testid="today-attention"]').innerText().catch(() => ""),
  };
  out.genericGone = !/你的下一座城市|已被充分考虑/.test(await page.locator("body").innerText());
  await page.screenshot({ path: SHOTS + "/T1_today_390.png", fullPage: true });
  console.log(JSON.stringify(out, null, 1));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

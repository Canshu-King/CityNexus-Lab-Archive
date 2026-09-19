const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
(async () => {
  await fetch("http://127.0.0.1:8000/api/v1/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  const out = {};

  // 1) 后端断开：拦截所有 /api/v1 请求
  await page.route("**/api/v1/**", (route) => route.abort("failed"));
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  const offText = (await page.locator("body").innerText()).replace(/\n+/g, " | ");
  out.offline_text = offText.slice(0, 300);
  out.offline_white = offText.trim().length < 40;
  out.offline_boundary = await page.locator('[data-testid="product-error-boundary"]').count() > 0;
  await page.screenshot({ path: SHOTS + "/80_backend_offline.png" });

  // 2) 恢复后端
  await page.unroute("**/api/v1/**");
  await page.reload({ waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);
  const onText = (await page.locator("body").innerText()).replace(/\n+/g, " | ");
  out.recovered_text = onText.slice(0, 200);
  out.recovered_ok = onText.includes("Today") && !onText.includes("出了点问题");
  await page.screenshot({ path: SHOTS + "/81_backend_recovered.png" });

  out.errors = errors.slice(0, 6);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walkB.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

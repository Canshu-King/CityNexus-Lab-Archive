const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
(async () => {
  await fetch("http://127.0.0.1:8000/api/v1/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  const out = {};

  // 语言切换 CN -> EN -> CN
  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  out.zh_head = (await page.locator("body").innerText()).slice(0, 60).replace(/\n+/g, " | ");
  const langBtn = page.locator('[data-testid="topbar-language"], [data-testid="home-language"]').first();
  await langBtn.click().catch(() => {});
  await page.waitForTimeout(1200);
  out.en_head = (await page.locator("body").innerText()).slice(0, 60).replace(/\n+/g, " | ");
  await page.screenshot({ path: SHOTS + "/90_lang_en.png" });
  await langBtn.click().catch(() => {});
  await page.waitForTimeout(1200);
  out.zh2_head = (await page.locator("body").innerText()).slice(0, 60).replace(/\n+/g, " | ");
  out.itinerary_still_there = await page.locator('[data-testid="trip-itinerary"], [data-testid="trip-itinerary-empty"]').count() > 0;

  // GPS 拒绝
  const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, permissions: [] });
  const p2 = await ctx2.newPage();
  const e2 = []; p2.on("pageerror", (e) => e2.push(String(e).slice(0, 160)));
  await p2.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  await p2.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await p2.waitForTimeout(2000);
  const cta = p2.locator(".v8-locate-button, [data-testid=locate]").first();
  if (await cta.count()) { await cta.click().catch(() => {}); await p2.waitForTimeout(2000); }
  const gpsText = (await p2.locator("body").innerText()).replace(/\n+/g, " | ");
  out.gps_denied_ok = gpsText.length > 100;             // 仍能规划，不是白屏
  out.gps_text = gpsText.slice(0, 140);
  out.gps_errors = e2.slice(0, 4);
  await p2.screenshot({ path: SHOTS + "/91_gps_denied.png" });

  out.errors = errors.slice(0, 5);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walkC.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

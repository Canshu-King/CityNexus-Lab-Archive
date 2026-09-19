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
  page.on("console", (m) => { if (m.type() === "error") errors.push("C: " + m.text().slice(0, 160)); });
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const out = {};
  // Copilot dock 与底部导航是否重叠
  const dock = await page.locator(".cn-copilot-dock").boundingBox().catch(() => null);
  const nav = await page.locator(".v8-mobile-nav").boundingBox().catch(() => null);
  out.dock = dock; out.nav = nav;
  out.overlap = dock && nav ? Math.max(0, Math.round((dock.y + dock.height) - nav.y)) : null;

  // 打开 Copilot，量面板高度占比
  await page.locator(".cn-copilot-edge").click().catch(() => {});
  await page.waitForTimeout(900);
  const panel = await page.locator(".cn-copilot-panel").boundingBox().catch(() => null);
  out.panel = panel;
  out.panel_pct_of_screen = panel ? Math.round((panel.height / 844) * 100) : null;
  await page.screenshot({ path: SHOTS + "/30_copilot_open.png" });
  await page.keyboard.press("Escape").catch(() => {});
  await page.locator(".cn-copilot-close").click().catch(() => {});
  await page.waitForTimeout(500);

  // Today 画面文本
  out.hub_text = (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 300);
  await page.screenshot({ path: SHOTS + "/31_today.png" });
  out.errors = errors.slice(0, 6);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk3.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("CONSOLE: " + m.text().slice(0, 200)); });

  const out = {};

  // 1) 首次打开 "/"
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  out.root_url = page.url();
  const body = (await page.locator("body").innerText()).slice(0, 500);
  out.root_text = body.replace(/\n+/g, " | ");
  out.looks_legacy = /LegacyApp|Travel Wallet|V10|Recovery|Authoritative trip execution/i.test(body);
  // 底部导航
  const nav = page.locator(".v8-mobile-nav button");
  out.mobile_nav_count = await nav.count();
  out.mobile_nav_labels = [];
  for (let i = 0; i < out.mobile_nav_count; i++) out.mobile_nav_labels.push((await nav.nth(i).innerText()).trim());
  await page.screenshot({ path: SHOTS + "/01_root_390.png", fullPage: false });

  out.errors = errors.slice(0, 10);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/audit1.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

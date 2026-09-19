const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";

async function api(path, init) {
  const r = await fetch("http://127.0.0.1:8000/api/v1" + path, {
    headers: { "Content-Type": "application/json" }, ...init,
  });
  let b = null; try { b = await r.json(); } catch {}
  return { status: r.status, body: b };
}

(async () => {
  await api("/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C: " + m.text().slice(0, 160)); });
  await page.addInitScript(() => {
    window.localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222");
  });

  const out = { tabs: [] };
  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const nav = page.locator(".v8-mobile-nav button");
  out.nav_count = await nav.count();
  out.nav_labels = [];
  for (let i = 0; i < out.nav_count; i++) out.nav_labels.push((await nav.nth(i).innerText()).trim());
  await page.screenshot({ path: SHOTS + "/02_today_390.png" });

  // 逐个点击主 tab
  const keys = ["hub", "trips", "map", "agent", "me"];
  for (const k of keys) {
    const before = errors.length;
    await page.goto(BASE + "/v8/" + k, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(1800);
    const text = await page.locator("body").innerText();
    out.tabs.push({
      key: k,
      text_len: text.length,
      white_screen: text.trim().length < 40,
      has_raw_enum: /REQUEST_PLACE_SEARCH|PlanVersion|semantic_key|C4_Anchored|deterministic gate|provider evidence/i.test(text),
      head: text.replace(/\n+/g, " | ").slice(0, 220),
      new_errors: errors.slice(before, before + 3),
    });
    await page.screenshot({ path: `${SHOTS}/03_tab_${k}_390.png` });
  }

  out.errors = errors.slice(0, 12);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/audit2b.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

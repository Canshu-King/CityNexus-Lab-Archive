const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const out = {};
  // A) 无 demo journey，全新用户 -> 地图 tab 应给诚实空态（不是天津）
  const c1 = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  const p1 = await c1.newPage();
  const e1 = []; p1.on("pageerror", (e) => e1.push(String(e).slice(0, 160)));
  await p1.addInitScript(() => localStorage.clear());
  await p1.goto(BASE + "/v8/map", { waitUntil: "networkidle", timeout: 60000 });
  await p1.waitForTimeout(2500);
  out.no_journey_map = {
    text: (await p1.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 200),
    errors: e1.slice(0, 4),
  };
  await p1.screenshot({ path: SHOTS + "/20_map_no_journey.png" });
  await c1.close();

  // B) demo journey -> 地图 tab
  await fetch("http://127.0.0.1:8000/api/v1/demo/reset", { method: "POST" });
  const c2 = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  const p2 = await c2.newPage();
  const e2 = []; p2.on("pageerror", (e) => e2.push(String(e).slice(0, 160)));
  await p2.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  await p2.goto(BASE + "/v8/map", { waitUntil: "networkidle", timeout: 60000 });
  await p2.waitForTimeout(3000);
  out.demo_map = {
    empty_state: await p2.locator('[data-testid="v8-map-empty"]').count() > 0,
    map_panel: await p2.locator('[data-testid="v8-maplibre-panel"]').count() > 0,
    text: (await p2.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 200),
    errors: e2.slice(0, 4),
  };
  await p2.screenshot({ path: SHOTS + "/21_map_demo.png" });
  await c2.close();
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk2.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

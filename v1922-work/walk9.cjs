const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const JID = "22222222-2222-4222-8222-222222222222";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
async function api(p, init) {
  const r = await fetch(API + p, { headers: { "Content-Type": "application/json" }, ...init });
  let b = null; try { b = await r.json(); } catch {}
  return { status: r.status, body: b };
}
(async () => {
  await api("/demo/reset", { method: "POST" });
  const out = {};
  const gen = await api(`/journeys/${JID}/plans/generate`, { method: "POST", body: "{}" });
  out.generate = gen.status;
  const plans = await api(`/journeys/${JID}/plans`);
  out.plans = Array.isArray(plans.body) ? plans.body.length : 0;
  if (out.plans) {
    const sel = await api(`/journeys/${JID}/plans/${plans.body[0].id}/select`, { method: "POST" });
    out.select = sel.status;
  }
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C: " + m.text().slice(0, 160)); });
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const txt = (await page.locator("body").innerText()).replace(/\n+/g, " | ");
  out.trips_len = txt.length;
  out.trips_text = txt.slice(0, 900);
  out.day_cards = await page.locator(".v8-day-detail").count();
  await page.screenshot({ path: SHOTS + "/71_trips_with_plan.png", fullPage: true });
  out.errors = errors.slice(0, 5);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk9.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

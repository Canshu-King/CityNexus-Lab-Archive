/** Shared helpers for the autonomous product-discovery cycles. */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");

const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/shots";

async function api(method, p, body) {
  const r = await fetch(API + p, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `lab-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  let json = null;
  try { json = JSON.parse(text); } catch { json = { _raw: text.slice(0, 400) }; }
  return { status: r.status, json };
}

async function launch() {
  const browser = await chromium.launch({
    channel: "chrome",
    args: ["--disable-dev-shm-usage", "--no-sandbox", "--js-flags=--max-old-space-size=2048"],
  });
  return browser;
}

async function context(browser) {
  return browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, locale: "zh-CN",
  });
}

function attachErrors(page, errors) {
  page.on("pageerror", (e) => errors.push("pageerror:" + String(e).slice(0, 200)));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError|Failed to load resource|net::ERR/.test(m.text()))
      errors.push("console:" + m.text().slice(0, 200));
  });
}

/** Create a journey through the visible 3-step wizard. Returns the journey id. */
async function wizardCreate(page, opts = {}) {
  const city = opts.city || "厦门";
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  // A prior journey may exist in this profile: force the setup sheet.
  if (!(await page.locator('[data-testid="trial-city"]').count())) {
    const newBtn = page.getByRole("button", { name: /试用其他城市|Try another city/ });
    if (await newBtn.count()) { await newBtn.first().click(); await page.waitForTimeout(1200); }
    else await page.goto(BASE + "/v8/me", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    const nb2 = page.getByRole("button", { name: /试用其他城市|Try another city/ });
    if (await nb2.count()) { await nb2.first().click(); await page.waitForTimeout(1200); }
  }
  await page.locator('[data-testid="trial-city"]').fill(city);
  await page.waitForTimeout(400);
  const inferred = await page.locator('[data-testid="trial-inferred"]').innerText().catch(() => "");
  await page.locator('[data-testid="trial-arrival"]').fill(opts.arrival || `${city}高崎国际机场`);
  await page.locator('[data-testid="trial-departure"]').fill(opts.departure || `${city}北站`);
  await page.locator('[data-testid="trial-start"]').fill(opts.start || "2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill(opts.end || "2026-11-08T20:00");
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  if (opts.party) await page.locator('[data-testid="trial-party"]').fill(String(opts.party));
  await page.locator('[data-testid="trial-budget"]').fill(String(opts.budget ?? 3000));
  await page.locator('[data-testid="trial-stay-budget"]').fill(String(opts.stayBudget ?? 1000));
  if (opts.special) await page.locator('[data-testid="trial-special"]').fill(opts.special);
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-create"]').click();
  // Journey creation runs the real stay capture; wait for the wizard to close
  // instead of sampling once, otherwise the harness reads an id too early.
  let jid = null;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(2000);
    jid = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    const stillSetup = await page.locator('[data-testid="trial-create"]').count();
    if (jid && !stillSetup) break;
  }
  await page.waitForTimeout(2000);
  return { jid, inferred };
}

/** Open the AI sheet, submit `text`, wait for a real plan count. Returns {count, text}. */
async function runAiPlan(page, text) {
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="hub-plan-with-ai"]').click();
  await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill(text);
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let count = -1, out = "";
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    out = await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "");
    if (n !== null) { count = Number(n); break; }
  }
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1500);
  return { count, text: out };
}

/** Choose the first candidate plan through the comparison UI. */
async function chooseFirstPlan(page) {
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  const bands = [];
  for (let i = 0; i < cards; i++)
    bands.push((await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")).trim());
  if (cards === 0) return { cards, bands, chosen: false };
  await page.locator('[data-testid="plan-cmp-choose"]').first().click();
  let chosen = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(1500);
    if (!(await page.locator('[data-testid="plan-comparison"]').count())) { chosen = true; break; }
  }
  await page.waitForTimeout(2500);
  return { cards, bands, chosen };
}


/** Create a journey whose stay capture actually produced options (OSM can be cold). */
async function wizardCreateWithOptions(page, opts = {}) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const created = await wizardCreate(page, opts);
    if (!created.jid) continue;
    for (let i = 0; i < 12; i++) {
      const r = await api("GET", `/journeys/${created.jid}/experience`);
      if (r.status === 200 && (r.json.options ?? []).length > 0) return created;
      await page.waitForTimeout(5000);
    }
  }
  return { jid: null };
}

module.exports = { api, launch, context, attachErrors, wizardCreate, wizardCreateWithOptions, runAiPlan, chooseFirstPlan, BASE, API, EV, SHOTS, fs };

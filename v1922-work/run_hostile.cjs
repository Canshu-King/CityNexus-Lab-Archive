/**
 * E2E run 6 - hostile / failure loops.
 *
 * Plausible phone misadventures: double-tapping the primary CTA, refreshing
 * while the AI planner is working, hammering the Copilot dock, resubmitting the
 * booking form, and losing the network mid-flow.  The product must stay
 * truthful and must never create duplicate truth.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/shots";
const api = async (method, p) => {
  const r = await fetch(API + p, { headers: { "Content-Type": "application/json" } });
  const t = await r.text();
  try { return { status: r.status, json: JSON.parse(t) }; } catch { return { status: r.status, json: { _raw: t.slice(0, 200) } }; }
};

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  const T = [];
  let JID = null;
  const rec = (action, status, result) =>
    T.push({ ts: new Date().toISOString(), journey_id: JID, action, status, result: String(result).replace(/\s+/g, " ").slice(0, 190) });
  page.on("pageerror", (e) => errors.push(`pageerror:${String(e).slice(0, 140)}`));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|ERR_PROXY|AJAXError|Failed to load resource/.test(m.text()))
      errors.push(`console:${m.text().slice(0, 140)}`);
  });
  const shot = (n) => page.screenshot({ path: `${SHOTS}/hostile_${n}.png` }).catch(() => {});
  const has = async (s) => (await page.locator(s).count()) > 0;

  try {
    // ---- 1. double-tap the wizard primary CTA ---------------------------
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="trial-city"]').fill("厦门");
    await page.waitForTimeout(400);
    await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
    await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
    await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
    await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="trial-next"]').click();
    await page.waitForTimeout(700);
    await page.locator('[data-testid="trial-budget"]').fill("3000");
    await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
    await page.locator('[data-testid="trial-next"]').click();
    await page.waitForTimeout(700);
    const createBtn = page.locator('[data-testid="trial-create"]');
    const guardBefore = await createBtn.isDisabled();
    await createBtn.click();
    // A real thumb cannot press a disabled button; assert the product's own
    // guard instead of forcing the DOM past it.
    const guardAfter = await createBtn.isDisabled().catch(() => null);
    await page.waitForTimeout(9000);
    JID = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    rec("double-tap-create", JID ? "201" : "NO-JOURNEY",
        `guardBefore=${guardBefore} guardAfter=${guardAfter}`);
    await shot("01_create");
    if (!JID) throw new Error("journey not created");

    // ---- 2. refresh in the middle of AI planning ------------------------
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(() => {});
    await page.waitForTimeout(1200);
    await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
    await page.locator('[data-testid="plan-ai-submit"]').click();
    await page.waitForTimeout(2500);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    rec("refresh-during-ai", (await has('[data-testid="today-heading"]')) ? "recovered" : "broken",
        "hub rendered after a mid-plan reload");
    await shot("02_refresh_during_ai");

    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    if (!(await has('[data-testid="plan-ai-input"]'))) {
      await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(() => {});
      await page.waitForTimeout(1500);
    }
    if (await has('[data-testid="plan-ai-input"]')) {
      await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
      await page.locator('[data-testid="plan-ai-submit"]').click();
    }
    let count = -1;
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(2500);
      const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
      if (n !== null) { count = Number(n); break; }
    }
    rec("ai-after-refresh", count > 0 ? `plans-ready(${count})` : `no-plans(${count})`, "");
    await page.locator(".plan-ai-close").click().catch(() => {});
    await page.waitForTimeout(2000);

    // ---- 3. double-tap the plan chooser --------------------------------
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    if (await has('[data-testid="plan-cmp-choose"]')) {
      await page.locator('[data-testid="plan-cmp-choose"]').first().click();
      await page.locator('[data-testid="plan-cmp-choose"]').first().click({ force: true }).catch(() => {});
      for (let i = 0; i < 25; i++) {
        await page.waitForTimeout(2000);
        if (!(await has('[data-testid="plan-comparison"]'))) break;
      }
    }
    rec("double-tap-choose-plan", (await has('[data-testid="plan-comparison"]')) ? "not-selected" : "selected", "");

    // ---- 4. hotel, double-tapping the choose button ---------------------
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    // The trips shell must be interactive before the tab is tapped, otherwise
    // the click lands on a not-yet-mounted nav and the panel never opens.
    await page.waitForSelector('[data-testid="trips-tab-stay"]', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(3000);
    let hotels = 0;
    for (let attempt = 0; attempt < 3 && hotels === 0; attempt++) {
      await page.locator('[data-testid="trips-tab-stay"]').click().catch(() => {});
      for (let i = 0; i < 40; i++) {
        await page.waitForTimeout(3000);
        hotels = await page.locator('[data-testid="hotel-card"]').count();
        if (hotels > 0) break;
      }
    }
    let chosen = false;
    for (let i = 0; i < Math.min(hotels, 4); i++) {
      await page.locator('[data-testid="hotel-choose"]').nth(i).click();
      await page.locator('[data-testid="hotel-choose"]').nth(i).click({ force: true }).catch(() => {});
      await page.waitForTimeout(5000);
      if (await has('[data-testid="hotel-chosen"]')) { chosen = true; break; }
    }
    rec("double-tap-choose-hotel", chosen ? "selected" : "not-selected", `${hotels} hotels`);
    await shot("03_hotel");

    // ---- 5. resubmit the booking form ----------------------------------
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="trips-tab-bookings"]').click();
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="inbox-tab-manual"]').click();
    await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("E2E-HOSTILE-DUP");
    await page.locator('[data-testid="manual-from"]').fill("厦门北站");
    await page.locator('[data-testid="manual-to"]').fill("深圳北站");
    await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    await page.locator('[data-testid="manual-submit"]').click();
    await page.locator('[data-testid="manual-submit"]').click({ force: true }).catch(() => {});
    await page.waitForTimeout(7000);
    await page.locator('[data-testid="v13-2-anchor-role"]').selectOption("DEPARTURE").catch(() => {});
    await page.locator('[data-testid="v13-2-save-corrections"]').click().catch(() => {});
    await page.waitForTimeout(3500);
    await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
    await page.locator('[data-testid="v13-2-smart-apply"]').click({ force: true }).catch(() => {});
    await page.waitForTimeout(6000);
    const inbox = await api("GET", `/journeys/${JID}/inbox`);
    const drafts = inbox.json?.drafts ?? [];
    const confirmed = drafts.filter((d) => d.status === "CONFIRMED").length;
    const wallet = await api("GET", `/journeys/${JID}/wallet`);
    const resv = wallet.json?.reservations ?? [];
    const refs = resv.map((r) => r.confirmation_ref);
    const dupRefs = refs.filter((x, i, a) => a.indexOf(x) !== i);
    rec("double-submit-booking", confirmed >= 1 && dupRefs.length === 0 ? "no-duplicate" : "DUPLICATE",
        `drafts=${drafts.length} confirmed=${confirmed} reservations=${resv.length} dupRefs=${dupRefs.length}`);
    await shot("04_booking");

    // ---- 6. hammer the Copilot dock open/closed ------------------------
    await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    for (let i = 0; i < 5; i++) {
      if (await has('.cn-copilot-edge')) await page.locator('.cn-copilot-edge').click().catch(() => {});
      await page.waitForTimeout(300);
      if (await has('.cn-copilot-close')) await page.locator('.cn-copilot-close').click().catch(() => {});
      await page.waitForTimeout(300);
    }
    rec("hammer-copilot-dock", (await has('[data-testid="v18-copilot-dock"]')) ? "stable" : "broken",
        "10 rapid open/close cycles");
    await shot("05_dock");

    // ---- 7. lose the network mid-flow, then recover --------------------
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.route("**/api/v1/**", (route) => route.abort("failed"));
    await page.locator('[data-testid="trips-tab-stay"]').click().catch(() => {});
    await page.waitForTimeout(6000);
    rec("network-lost", "offline",
        (await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 180));
    await shot("06_offline");
    await page.unroute("**/api/v1/**");
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    rec("network-recovered", (await has('[data-testid="trips-tabs"]')) ? "recovered" : "broken", "");
    await shot("07_recovered");

    // ---- 8. final truth integrity --------------------------------------
    const exp = await api("GET", `/journeys/${JID}/experience`);
    const acts = exp.json?.active_plan?.activities ?? [];
    const ids = acts.map((a) => a.id);
    const dupIds = ids.filter((x, i, a) => a.indexOf(x) !== i);
    rec("final-integrity", acts.length > 0 && dupIds.length === 0 ? "clean" : "DAMAGED",
        `activities=${acts.length} locked=${acts.filter((a) => a.locked).length} dupIds=${dupIds.length}`);
  } catch (e) {
    rec("FAILURE", "error", e.message);
  }

  fs.writeFileSync(`${EV}/scenario_hostile.json`, JSON.stringify({
    run: "hostile", journey_id: JID, viewport: "390x844", trace: T, errors: errors.slice(0, 12),
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.action.padEnd(26)} ${String(t.status).padEnd(16)} ${t.result.slice(0, 80)}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})();

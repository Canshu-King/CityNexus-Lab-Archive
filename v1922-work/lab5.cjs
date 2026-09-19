/**
 * Five autonomous product-lab cycles, run compactly against the live system.
 * Each cycle states a hypothesis, probes it through the real UI/API, and
 * records the observed evidence.  Reports are written by lab5_report.py.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const J = JSON.parse(fs.readFileSync(EV + "/scenario_degraded.json", "utf8")).journey_id;
const out = { journey: J, cycles: [] };
const api = async (m, p) => {
  const r = await fetch(API + p, { headers: { "Content-Type": "application/json" } });
  const t = await r.text();
  try { return { status: r.status, json: JSON.parse(t) }; } catch { return { status: r.status, json: null, raw: t.slice(0, 200) }; }
};

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });

  // ---- CYCLE 1: does a plan survive hard refresh + navigation? -----------
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
    const before = await api("GET", `/journeys/${J}/experience`);
    const b = (before.json?.active_plan?.activities ?? []).length;
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const after = await api("GET", `/journeys/${J}/experience`);
    const a = (after.json?.active_plan?.activities ?? []).length;
    const bIds = (before.json?.active_plan?.activities ?? []).map((x) => x.id).join(",");
    const aIds = (after.json?.active_plan?.activities ?? []).map((x) => x.id).join(",");
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="nav-trips"]').click();
    await page.waitForTimeout(2500);
    await page.goBack(); await page.waitForTimeout(2500);
    await page.goForward(); await page.waitForTimeout(2500);
    const tabs = await page.locator('[data-testid="trips-tabs"]').count();
    out.cycles.push({
      n: 1, hypothesis: "A chosen plan survives hard refresh, back and forward without drift",
      method: "Load Trips, reload, then navigate hub->trips->back->forward; compare the plan before/after via the API",
      evidence: { activitiesBefore: b, activitiesAfter: a, identicalIds: bIds === aIds, tripsTabsAfterNavigation: tabs },
    });
    await ctx.close();
  }

  // ---- CYCLE 2: empty / degraded honesty --------------------------------
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    await page.addInitScript(() => localStorage.clear());
    const screens = {};
    for (const r of ["/v8/hub", "/v8/agent", "/v8/trips", "/v8/live"]) {
      await page.goto(BASE + r, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(4500);
      screens[r] = (await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 130);
    }
    await ctx.close();
    const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const p2 = await ctx2.newPage();
    await p2.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
    await p2.route("**/api/v1/**", (r) => r.abort("failed"));
    await p2.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await p2.waitForTimeout(5000);
    await p2.locator('[data-testid="trips-tab-stay"]').click().catch(() => {});
    await p2.waitForTimeout(5000);
    const offline = (await p2.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 160);
    await ctx2.close();
    const leaks = Object.entries(screens).filter(([, v]) =>
      /UNKNOWN_REALTIME|REQUEST_|AUTO_APPLY|C4_|TIANJIN|DeepSeek|Hermes|Semantic:|Execution:|WALK|BICYCLE|TRANSIT|RIDE_HAIL/.test(v));
    out.cycles.push({
      n: 2, hypothesis: "No screen is ever blank, and no internal enum leaks into the Chinese UI",
      method: "Visit hub/agent/trips/live with no journey, then with a journey and the API blocked",
      evidence: { noTrip: screens, offlineWithApiBlocked: offline, internalLeaks: leaks.map(([k]) => k) },
    });
  }

  // ---- CYCLE 3: cross-surface agreement after replan --------------------
  {
    const exp = await api("GET", `/journeys/${J}/experience`);
    const acts = exp.json?.active_plan?.activities ?? [];
    const ids = acts.map((a) => a.id);
    const dupIds = ids.filter((x, i, arr) => arr.indexOf(x) !== i);
    const locked = acts.filter((a) => a.locked);
    const times = acts.map((a) => a.start_at);
    const sorted = [...times].sort();
    const chrono = JSON.stringify(times) === JSON.stringify(sorted);
    const props = await api("GET", `/journeys/${J}/replans`);
    const accepted = (props.json ?? []).filter((p) => p.status === "ACCEPTED").length;
    out.cycles.push({
      n: 3, hypothesis: "After accepting a replan, Trips/Live/backend agree and no locked commitment was moved or dropped",
      method: "Read the authoritative plan and the replan history after the accepted disruption",
      evidence: { activities: acts.length, locked: locked.length, duplicateIds: dupIds.length, chronological: chrono, acceptedReplans: accepted },
    });
  }

  // ---- CYCLE 4: budget honesty ------------------------------------------
  {
    const low = await api("GET", `/journeys/${J}/plans`);
    const plans = low.json ?? [];
    const bands = [];
    for (const p of plans) {
      const cost = p.total_cost_minor ?? 0;
      const journey = await api("GET", `/journeys/${J}`);
      const budget = journey.json?.budget?.amount_minor ?? 0;
      bands.push({ id: String(p.id).slice(0, 8), cost, budget, ratio: budget ? +(cost / budget).toFixed(3) : null });
    }
    const unknownPrices = (await api("GET", `/journeys/${J}/stay-options`)).json?.offers?.filter((o) => o.total_amount_minor === 0).length ?? 0;
    out.cycles.push({
      n: 4, hypothesis: "The product states the budget relationship truthfully and shows unknown prices as unknown, never as 0",
      method: "Compare each candidate plan cost against the journey budget; count offers whose price is absent",
      evidence: { planBands: bands, offersWithNoPrice: unknownPrices },
    });
  }

  // ---- CYCLE 5: input robustness ----------------------------------------
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
    const page = await ctx.newPage();
    await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
    const errs = [];
    page.on("pageerror", (e) => errs.push(String(e).slice(0, 120)));
    await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator(".cn-copilot-edge").click().catch(() => {});
    await page.waitForTimeout(1200);
    const box = page.locator(".cn-copilot-form textarea");
    const longText = "厦门".repeat(400);
    let longOk = false;
    if (await box.count()) {
      await box.fill(longText);
      await page.locator('.cn-copilot-form button[type="submit"]').click().catch(() => {});
      await page.waitForTimeout(9000);
      longOk = (await page.locator("body").innerText()).length > 200;
    }
    // Repeated open/close must not break the dock.
    for (let i = 0; i < 4; i++) {
      if (await page.locator(".cn-copilot-close").count()) await page.locator(".cn-copilot-close").click().catch(() => {});
      await page.waitForTimeout(250);
      if (await page.locator(".cn-copilot-close").count()) await page.locator(".cn-copilot-close").click().catch(() => {});
      await page.waitForTimeout(250);
      if (await page.locator(".cn-copilot-edge").count()) await page.locator(".cn-copilot-edge").click().catch(() => {});
      await page.waitForTimeout(250);
    }
    const dockOk = (await page.locator('[data-testid="v18-copilot-dock"]').count()) > 0;
    await ctx.close();
    out.cycles.push({
      n: 5, hypothesis: "Extreme input and repeated dock toggling never break the surface",
      method: "Submit a very long Copilot question, then toggle the dock eight times",
      evidence: { longInputSurvived: longOk, dockStable: dockOk, pageErrors: errs.length },
    });
  }

  fs.writeFileSync(EV + "/LAB_PROBE_RESULTS.json", JSON.stringify(out, null, 1), "utf8");
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})();

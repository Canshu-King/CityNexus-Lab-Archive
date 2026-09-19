/** CYCLE 2 focus — no-plan Hub "Plan at a glance" and Stay Explorer price honesty. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const R = {};
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);

  // ---- Hub with no chosen plan ----
  await p.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  R.hub = {
    heading: (await p.locator('[data-testid="today-heading"]').innerText().catch(() => "")).trim(),
    stay: (await p.locator('[data-testid="today-stay"]').innerText().catch(() => "")).trim(),
    next: (await p.locator('[data-testid="today-next"]').innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
    glance: (await p.locator(".v8-day-row").innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
    glanceCards: await p.locator(".v8-day-card").count(),
    comparisonVisible: await p.locator('[data-testid="plan-comparison"]').count(),
  };
  await p.screenshot({ path: `${SHOTS}/lab_2_C_hub_noplan_glance.png`, fullPage: true }).catch(() => {});

  // ---- Stay Explorer ----
  await p.goto(BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  R.stayExplorer = {
    body: (await p.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").trim().slice(0, 700),
    firstCard: (await p.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
    cards: await p.locator('[data-testid="stay-offer-card"]').count(),
  };
  await p.screenshot({ path: `${SHOTS}/lab_2_C_stay_explorer_noplan.png`, fullPage: true }).catch(() => {});

  // ---- backend truth for those options ----
  const stay = (await api("GET", `/journeys/${JID}/stay-options`)).json;
  R.backend = (stay.options ?? []).slice(0, 3).map((o) => ({
    property_name: o.stay.property_name, total: o.stay.total_amount_minor, nightly: o.stay.nightly_amount_minor,
    currency_explicit: o.stay.evidence?.currency_explicit, price_basis: o.stay.evidence?.price_basis, status: o.status,
  }));
  R.todayStayBackend = (await api("GET", `/journeys/${JID}/experience`)).json.selected_option_id;
  R.errors = errs.slice(0, 6);
  fs.writeFileSync(`${EV}/cycle2_focus.json`, JSON.stringify(R, null, 1), "utf8");
  console.log(JSON.stringify(R, null, 1));
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

/**
 * Is the "over budget" verdict reachable and truthful?
 *
 * The live OSM city carries no prices, so a genuine over-budget verdict cannot
 * arise from it.  This probe drives the real discovery endpoint for a city
 * whose sealed fixture carries real activity prices, then reads the comparison
 * cards for a tiny budget.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const JID = process.argv[2];

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  await page.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const out = { jid: JID };

  // ask the real discovery endpoint to materialise places for this city
  const disc = await api("POST", `/journeys/${JID}/real-city/discover`, {
    query: "\u57ce\u5e02\u89c2\u5149", radius_m: 5000, limit: 8, mode: "live",
  });
  out.discoveryStatus = disc.status;
  out.discoveryProviders = disc.json?.provider_status ?? null;
  const places = await api("GET", `/places?city_code=CN-TIANJIN`);
  out.places = Array.isArray(places.json) ? places.json.length : places.json;

  // now plan through the UI
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u5929\u6d25\uff0c\u60f3\u770b\u770b\u57ce\u5e02\uff0c\u9884\u7b97\u5f88\u7d27\u3002");
  out.aiPlanCount = ai.count;
  out.aiText = ai.text.slice(0, 200);

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  out.cards = cards;
  out.bands = [];
  out.totals = [];
  out.whys = [];
  for (let i = 0; i < cards; i++) {
    out.bands.push(clean(await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")));
    out.totals.push(clean(await page.locator('[data-testid="plan-cmp-card"]').nth(i).locator("dd").first().innerText().catch(() => "")));
    const why = page.locator(".plan-cmp-why").nth(i);
    out.whys.push((await why.count()) ? clean(await why.innerText().catch(() => "")) : "");
  }
  out.comparisonText = clean(await page.locator('[data-testid="plan-comparison"]').innerText().catch(() => "")).slice(0, 420);
  await page.screenshot({ path: `${SHOTS}/lab_5_G_tianjin_budget.png`, fullPage: true }).catch(() => {});

  const plans = (await api("GET", `/journeys/${JID}/plans`)).json;
  out.backendPlans = (plans ?? []).map((p) => ({
    v: p.version_no, status: p.status, total: p.total_cost?.amount_minor,
    known: (p.activities ?? []).filter((a) => ["KNOWN", "KNOWN_FREE", "KNOWN_PAID"].includes(String(a.cost_status ?? "").toUpperCase())).length,
    unknown: (p.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
    stops: (p.activities ?? []).length,
  }));
  out.errors = errs.slice(0, 5);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle5_over_budget.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

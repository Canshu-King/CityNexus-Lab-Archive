/**
 * Can the within/near/over verdict be exercised at all?
 * A city whose sealed fixture carries real prices is created through the
 * normal wizard (a traveller typing the city), then a tiny budget is used so a
 * genuine "over budget" verdict must appear with a reason.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  const out = { cases: [] };

  for (const spec of [
    { city: "\u5929\u6d25", budget: 400, stayBudget: 200, label: "tiny-budget" },
    { city: "\u5929\u6d25", budget: 20000, stayBudget: 10000, label: "generous-budget" },
  ]) {
    const c = await L.wizardCreateWithOptions(page, { city: spec.city, budget: spec.budget, stayBudget: spec.stayBudget, arrival: `${spec.city}站`, departure: `${spec.city}机场` });
    const rec = { label: spec.label, city: spec.city, budgetCny: spec.budget, jid: c.jid };
    if (!c.jid) { rec.failed = "no journey"; out.cases.push(rec); continue; }
    const ai = await L.runAiPlan(page, `\u7b2c\u4e00\u6b21\u6765${spec.city}\uff0c\u60f3\u770b\u770b\u57ce\u5e02\uff0c\u9884\u7b97${spec.budget}\u5143\u3002`);
    rec.aiPlanCount = ai.count;
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    rec.cards = cards;
    rec.bands = [];
    rec.totals = [];
    rec.whys = [];
    for (let i = 0; i < cards; i++) {
      rec.bands.push(clean(await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")));
      rec.totals.push(clean(await page.locator('[data-testid="plan-cmp-card"]').nth(i).locator("dd").first().innerText().catch(() => "")));
      const why = page.locator(".plan-cmp-why").nth(i);
      rec.whys.push((await why.count()) ? clean(await why.innerText().catch(() => "")) : "");
    }
    rec.comparisonText = clean(await page.locator('[data-testid="plan-comparison"]').innerText().catch(() => "")).slice(0, 420);
    await page.screenshot({ path: `${SHOTS}/lab_5_F_${spec.label}.png`, fullPage: true }).catch(() => {});
    const plans = (await api("GET", `/journeys/${c.jid}/plans`)).json;
    rec.backendPlans = (plans ?? []).map((p) => ({
      v: p.version_no, status: p.status, total: p.total_cost?.amount_minor,
      known: (p.activities ?? []).filter((a) => ["KNOWN", "KNOWN_FREE", "KNOWN_PAID"].includes(String(a.cost_status ?? "").toUpperCase())).length,
      unknown: (p.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
      stops: (p.activities ?? []).length,
    }));
    out.cases.push(rec);
    console.log(spec.label, JSON.stringify({ jid: c.jid, ai: rec.aiPlanCount, bands: rec.bands, totals: rec.totals }));
  }
  out.errors = errs.slice(0, 6);
  fs.writeFileSync(`${EV}/cycle5_priced_city.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

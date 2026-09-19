/**
 * CYCLE 5 - budget and honesty.
 *
 * A very low budget trip: does the product state the budget relationship
 * truthfully (within / near / over with a reason), and are unknown prices shown
 * as unknown rather than 0?
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const out = { cases: [], errors: [] };
const rec = (o) => { out.cases.push(o); console.log(JSON.stringify(o).slice(0, 700)); };

(async () => {
  const browser = await launch();

  // ---- A. very low budget: 300 CNY total / 100 stay ----
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = [];
    attachErrors(page, errs);
    const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 300, stayBudget: 100 });
    const jid = c.jid;
    const rec0 = { case: "A-low-budget", jid, budgetCny: 300, stayBudgetCny: 100 };
    if (!jid) { rec0.failed = "no journey"; rec(rec0); await ctx.close(); return; }
    const exp = (await api("GET", `/journeys/${jid}/experience`)).json;
    rec0.backendBudget = exp.journey.budget;
    rec0.backendStayBudget = exp.trip.stay_budget;

    const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u548c\u8001\u8857\uff0c\u9884\u7b97\u5f88\u7d27\u3002");
    rec0.aiPlanCount = ai.count;
    rec0.aiText = ai.text.slice(0, 200);

    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    const bands = [];
    const totals = [];
    const whys = [];
    for (let i = 0; i < cards; i++) {
      bands.push(clean(await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")));
      const dd = page.locator('[data-testid="plan-cmp-card"]').nth(i).locator("dd");
      totals.push(clean(await dd.first().innerText().catch(() => "")));
      const why = page.locator(".plan-cmp-why").nth(i);
      whys.push((await why.count()) ? clean(await why.innerText().catch(() => "")) : "");
    }
    rec0.comparison = { cards, bands, totals, whys };
    rec0.comparisonText = clean(await page.locator('[data-testid="plan-comparison"]').innerText().catch(() => "")).slice(0, 500);
    await page.screenshot({ path: `${SHOTS}/lab_5_A_low_budget_compare.png`, fullPage: true }).catch(() => {});

    // what does the backend say each candidate actually costs?
    const plans = (await api("GET", `/journeys/${jid}/plans`)).json;
    rec0.backendPlans = (plans ?? []).map((p) => ({
      v: p.version_no, status: p.status,
      total: p.total_cost,
      unknownStops: (p.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
      stops: (p.activities ?? []).length,
    }));

    // Spend tab must not fabricate a relationship either
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    await page.locator('[data-testid="trips-tab-spend"]').click();
    await page.waitForTimeout(6000);
    rec0.spendTab = clean(await page.locator('[data-testid="trips-spend"]').innerText().catch(() => "")).slice(0, 400);
    await page.screenshot({ path: `${SHOTS}/lab_5_A_low_budget_spend.png`, fullPage: true }).catch(() => {});

    rec0.errors = errs.slice(0, 5);
    rec(rec0);
    await ctx.close();
  }

  // ---- B. a comfortable budget, to compare the relationship ----
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = [];
    attachErrors(page, errs);
    const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 8000, stayBudget: 4000 });
    const jid = c.jid;
    const rec0 = { case: "B-comfortable-budget", jid, budgetCny: 8000 };
    const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
    rec0.aiPlanCount = ai.count;
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    const bands = [];
    const totals = [];
    for (let i = 0; i < cards; i++) {
      bands.push(clean(await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")));
      totals.push(clean(await page.locator('[data-testid="plan-cmp-card"]').nth(i).locator("dd").first().innerText().catch(() => "")));
    }
    rec0.comparison = { cards, bands, totals };
    await page.screenshot({ path: `${SHOTS}/lab_5_B_comfortable_compare.png`, fullPage: true }).catch(() => {});
    rec0.errors = errs.slice(0, 4);
    rec(rec0);
    await ctx.close();
  }

  // ---- C. unknown prices must never read as 0 anywhere ----
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = [];
    attachErrors(page, errs);
    const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
    const jid = c.jid;
    const rec0 = { case: "C-unknown-price-sweep", jid };
    const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u548c\u8001\u8857\u3002");
    rec0.aiPlanCount = ai.count;
    await L.chooseFirstPlan(page);
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3500);
    await page.locator('[data-testid="trips-tab-stay"]').click();
    let hotels = 0;
    for (let i = 0; i < 45; i++) {
      await page.waitForTimeout(5000);
      hotels = await page.locator('[data-testid="hotel-card"]').count();
      if (hotels > 0) break;
    }
    let pinned = false;
    for (let i = 0; i < Math.min(hotels, 8); i++) {
      await page.locator('[data-testid="hotel-choose"]').nth(i).click();
      await page.waitForTimeout(7000);
      if (await page.locator('[data-testid="hotel-chosen"]').count()) { pinned = true; break; }
    }
    rec0.hotelCards = hotels;
    rec0.pinned = pinned;

    const sweep = {};
    const scan = async (name, sel) => {
      const text = clean(await page.locator(sel).innerText().catch(() => ""));
      sweep[name] = { hasZeroYuan: /\u00a50\.00|CNY 0|CNY 0\.00/.test(text), snippet: text.slice(0, 220) };
    };
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    await scan("trips-itinerary", '[data-testid="trip-itinerary"]');
    await page.locator('[data-testid="trips-tab-spend"]').click();
    await page.waitForTimeout(6000);
    await scan("trips-spend", '[data-testid="trips-spend"]');
    await page.locator('[data-testid="trips-tab-bookings"]').click();
    await page.waitForTimeout(5000);
    await scan("trips-bookings", "body");
    await page.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    await scan("studio", '[data-testid="v8-trip-studio"]');
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    await scan("hub", "body");
    rec0.sweep = sweep;
    await page.screenshot({ path: `${SHOTS}/lab_5_C_unknown_price_sweep.png`, fullPage: true }).catch(() => {});

    // backend: how many stops / offers are genuinely unknown-priced
    const plans = (await api("GET", `/journeys/${jid}/plans`)).json;
    const active = (plans ?? []).find((p) => ["ACTIVE", "SELECTED"].includes(p.status));
    rec0.backend = {
      total: active?.total_cost,
      unknownStops: (active?.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
      stops: (active?.activities ?? []).length,
    };
    const stays = (await api("GET", `/journeys/${jid}/stay-options`)).json;
    rec0.backendStay = {
      options: (stays.options ?? []).length,
      zeroPriced: (stays.options ?? []).filter((o) => (o.stay?.nightly_amount_minor ?? 0) === 0).length,
      selected: (stays.options ?? []).filter((o) => o.status === "SELECTED").map((o) => o.stay.property_name),
    };
    rec0.errors = errs.slice(0, 5);
    rec(rec0);
    await ctx.close();
  }

  out.errors = [];
  fs.writeFileSync(`${EV}/cycle5.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  out.failure = e.message;
  fs.writeFileSync(`${EV}/cycle5.json`, JSON.stringify(out, null, 1), "utf8");
  process.exit(1);
});

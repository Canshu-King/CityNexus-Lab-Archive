/**
 * Can the product ever say "over budget", and does it say it truthfully?
 * Uses a deliberately tiny budget so the known mobility costs exceed it.
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
  const out = {};

  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 60, stayBudget: 20 });
  const jid = c.jid;
  out.jid = jid;
  out.budgetCny = 60;
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\uff0c\u9884\u7b97\u975e\u5e38\u7d27\u3002");
  out.aiPlanCount = ai.count;
  out.aiText = ai.text.slice(0, 160);

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
  out.comparisonText = clean(await page.locator('[data-testid="plan-comparison"]').innerText().catch(() => "")).slice(0, 460);
  await page.screenshot({ path: `${SHOTS}/lab_5_E_tiny_budget.png`, fullPage: true }).catch(() => {});

  // backend view
  const plans = (await api("GET", `/journeys/${jid}/plans`)).json;
  out.backendPlans = (plans ?? []).map((p) => ({
    v: p.version_no, status: p.status, total: p.total_cost,
    known: (p.activities ?? []).filter((a) => ["KNOWN", "KNOWN_FREE", "KNOWN_PAID"].includes(String(a.cost_status ?? "").toUpperCase())).length,
    unknown: (p.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
    stops: (p.activities ?? []).length,
  }));
  out.errors = errs.slice(0, 5);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle5_tiny_budget.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

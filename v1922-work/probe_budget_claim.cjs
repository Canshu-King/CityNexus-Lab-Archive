/**
 * Does the product claim "budget verified" when every price is unknown?
 * Compares the Studio feasibility claim against the actual cost evidence.
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

  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  const ap = exp.active_plan;
  const acts = ap?.activities ?? [];
  const plans = (await api("GET", `/journeys/${JID}/plans`)).json;
  const active = (plans ?? []).find((p) => p.id === ap?.id);
  out.backend = {
    planId: ap?.id,
    total: active?.total_cost ?? null,
    budget: exp.journey.budget,
    stops: acts.length,
    unknownStops: (active?.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
    knownStops: (active?.activities ?? []).filter((a) => ["KNOWN", "KNOWN_FREE", "KNOWN_PAID"].includes(String(a.cost_status ?? "").toUpperCase())).length,
    flags: exp.experience_flags,
  };

  await page.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.studio = {
    feasibility: clean(await page.locator(".v8-feasibility").innerText().catch(() => "")),
    costLines: clean(await page.locator(".v8-cost-lines").innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_5_D_studio_budget_claim.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  out.hub = clean(await page.locator("body").innerText().catch(() => "")).slice(0, 400);
  await page.screenshot({ path: `${SHOTS}/lab_5_D_hub.png`, fullPage: true }).catch(() => {});

  // Does the traveller get told anywhere that the budget relationship is unknown?
  const hasBudgetUnknownCopy = /\u9884\u7b97[\u672a\u65e0]\u6cd5|\u65e0\u6cd5\u5224\u65ad\u9884\u7b97|\u9884\u7b97\u672a\u77e5|budget unknown|cannot tell whether/i.test(out.studio.feasibility + out.hub);
  out.budgetUnknownCopy = hasBudgetUnknownCopy;
  out.claimsBudgetVerified = /\u9884\u7b97[\u5df2\u6838\u5bf9\u9a8c\u8bc1\u901a\u8fc7]|\u9884\u7b97[\u5df2\u9a8c\u8bc1]|budget.*verified/i.test(out.studio.feasibility);

  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle5_budget_claim.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

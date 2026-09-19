/**
 * CYCLE 5 final sweep: on a journey where no stop and no hotel has a provider
 * price, does ANY surface claim a budget relationship or print an unknown price
 * as 0?
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const JID = process.argv[2];

(async () => {
  const browser = await launch();
  const out = { jid: JID, surfaces: {}, errors: [] };

  // mobile surfaces
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    attachErrors(page, out.errors);
    await page.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
    const routes = [
      ["/v8/hub", "hub"],
      ["/v8/trips", "trips-itinerary"],
      ["/v8/live", "live"],
      ["/v8/map", "map"],
      ["/v8/agent", "copilot"],
      ["/v8/me", "me"],
      ["/v8/authoritative", "authoritative"],
      ["/v8/twin", "twin"],
      ["/v8/bookings", "wallet"],
    ];
    for (const [route, name] of routes) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(6000);
      const text = clean(await page.locator("body").innerText().catch(() => ""));
      out.surfaces[name] = {
        zeroYuan: /\u00a50\.00|CNY 0\b|CNY 0\.00/.test(text),
        claimsWithinBudget: /\u9884\u7b97\u5185|within budget/i.test(text),
        claimsOverBudget: /\u8d85\u9884\u7b97|over by/i.test(text),
        claimsBudgetVerified: /\u9884\u7b97[\u548c\uff0c]?\s*[\u5df2\u6838\u5bf9\u9a8c\u8bc1]|\u9884\u7b97\u5df2\u9a8c\u8bc1|budget.*verified/i.test(text),
        snippet: text.slice(0, 200),
      };
      await page.screenshot({ path: `${SHOTS}/lab_5_H_${name}.png`, fullPage: true }).catch(() => {});
    }
    // trips sub-tabs
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    for (const tab of ["itinerary", "stay", "bookings", "spend"]) {
      await page.locator(`[data-testid="trips-tab-${tab}"]`).click();
      await page.waitForTimeout(6000);
      const text = clean(await page.locator("body").innerText().catch(() => ""));
      out.surfaces[`trips-${tab}`] = {
        zeroYuan: /\u00a50\.00|CNY 0\b|CNY 0\.00/.test(text),
        claimsWithinBudget: /\u9884\u7b97\u5185|within budget/i.test(text),
        claimsOverBudget: /\u8d85\u9884\u7b97|over by/i.test(text),
        claimsBudgetVerified: /\u9884\u7b97[\u548c\uff0c]?\s*[\u5df2\u6838\u5bf9\u9a8c\u8bc1]|\u9884\u7b97\u5df2\u9a8c\u8bc1|budget.*verified/i.test(text),
        snippet: text.slice(0, 200),
      };
      await page.screenshot({ path: `${SHOTS}/lab_5_H_trips_${tab}.png`, fullPage: true }).catch(() => {});
    }
    await ctx.close();
  }

  // desktop surfaces (Studio + Stay Explorer are desktop routes)
  {
    const dctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "zh-CN" });
    const dp = await dctx.newPage();
    attachErrors(dp, out.errors);
    await dp.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
    for (const [route, name] of [["/v8/studio", "studio"], ["/v8/stay", "stay-explorer"]]) {
      await dp.goto(BASE + route, { waitUntil: "domcontentloaded" });
      await dp.waitForTimeout(8000);
      const text = clean(await dp.locator("body").innerText().catch(() => ""));
      out.surfaces[name] = {
        zeroYuan: /\u00a50\.00|CNY 0\b|CNY 0\.00/.test(text),
        claimsWithinBudget: /\u9884\u7b97\u5185|within budget/i.test(text),
        claimsOverBudget: /\u8d85\u9884\u7b97|over by/i.test(text),
        claimsBudgetVerified: /\u9884\u7b97[\u548c\uff0c]?\s*[\u5df2\u6838\u5bf9\u9a8c\u8bc1]|\u9884\u7b97\u5df2\u9a8c\u8bc1|budget.*verified/i.test(text),
        budgetNotVerified: /\u9884\u7b97\u672a\u9a8c\u8bc1/.test(text),
        snippet: text.slice(0, 240),
      };
      await dp.screenshot({ path: `${SHOTS}/lab_5_H_${name}.png`, fullPage: true }).catch(() => {});
    }
    await dctx.close();
  }

  // backend evidence
  const plans = (await api("GET", `/journeys/${JID}/plans`)).json;
  const active = (plans ?? []).find((p) => ["ACTIVE", "SELECTED"].includes(p.status));
  out.backend = {
    planTotalMinor: active?.total_cost?.amount_minor ?? null,
    stops: (active?.activities ?? []).length,
    pricedStops: (active?.activities ?? []).filter((a) => ["KNOWN", "KNOWN_FREE", "KNOWN_PAID"].includes(String(a.cost_status ?? "").toUpperCase())).length,
    unknownStops: (active?.activities ?? []).filter((a) => String(a.cost_status ?? "").toUpperCase() === "UNKNOWN").length,
    budget: (await api("GET", `/journeys/${JID}/experience`)).json.journey.budget,
  };
  out.anyZeroYuan = Object.entries(out.surfaces).filter(([, v]) => v.zeroYuan).map(([k]) => k);
  out.anyWithinBudgetClaim = Object.entries(out.surfaces).filter(([, v]) => v.claimsWithinBudget).map(([k]) => k);
  out.anyBudgetVerifiedClaim = Object.entries(out.surfaces).filter(([, v]) => v.claimsBudgetVerified).map(([k]) => k);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle5_sweep.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

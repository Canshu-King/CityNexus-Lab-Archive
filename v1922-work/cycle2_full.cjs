/** CYCLE 2 full re-verification after all empty/degraded-state fixes. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreateWithOptions, BASE, EV, SHOTS, fs } = L;
const R = { cases: [], errors: [] };
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const browser = await launch();

  // A. no journey at all
  {
    const ctx = await context(browser); const page = await ctx.newPage();
    const errs = []; attachErrors(page, errs);
    const out = { case: "A-no-journey", routes: {} };
    for (const route of ["/", "/v8/hub", "/v8/trips", "/v8/live", "/v8/agent", "/v8/map", "/v8/me", "/v8/stay", "/v8/bookings", "/v8/authoritative", "/v8/studio", "/v8/discover", "/v8/intelligence", "/v8/twin"]) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" }); await page.waitForTimeout(2500);
      const body = clean(await page.locator("body").innerText().catch(() => ""));
      out.routes[route] = { len: body.length, blank: body.length < 10, setup: await page.locator('[data-testid="trial-setup"]').count() };
    }
    out.blankRoutes = Object.entries(out.routes).filter(([, v]) => v.blank).map(([k]) => k);
    out.nonSetupRoutes = Object.entries(out.routes).filter(([, v]) => !v.setup).map(([k]) => k);
    out.errors = errs.slice(0, 5); R.cases.push(out);
    console.log("A blank=", out.blankRoutes, "nonSetup=", out.nonSetupRoutes);
    await ctx.close();
  }

  // B. journey, no chosen plan (mobile)
  const ctx = await context(browser); const page = await ctx.newPage();
  const errs = []; attachErrors(page, errs);
  const c = await wizardCreateWithOptions(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
  R.jid = c.jid;
  const out = { case: "B-no-plan", jid: c.jid };
  const exp0 = (await api("GET", `/journeys/${c.jid}/experience`)).json;
  out.backend = { active_plan: exp0.active_plan, selected_option_id: exp0.selected_option_id, options: (exp0.options ?? []).length };

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.hub = {
    caveat: clean(await page.locator('[data-testid="hub-glance-caveat"]').innerText().catch(() => "")),
    stay: clean(await page.locator('[data-testid="today-stay"]').innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_v2_hub_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.studio = {
    previewCaveat: clean(await page.locator('[data-testid="studio-preview-caveat"]').innerText().catch(() => "")),
    selectedStayBlock: await page.locator(".v8-selected-stay").count(),
    asideHeading: clean(await page.locator(".v8-aside-heading").innerText().catch(() => "")),
    stayTotal: clean(await page.locator('[data-testid="studio-stay-total"]').innerText().catch(() => "")),
    feasibility: clean(await page.locator(".v8-feasibility").innerText().catch(() => "")),
    noPlanChecked: await page.locator('[data-testid="studio-no-plan"]').count(),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_v2_studio_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-spend"]').click(); await page.waitForTimeout(6000);
  out.tripsSpend = { stayTotal: clean(await page.locator('[data-testid="spend-stay-total"]').innerText().catch(() => "")) };
  await page.screenshot({ path: `${SHOTS}/lab_2_v2_trips_spend.png`, fullPage: true }).catch(() => {});

  await page.locator('[data-testid="trips-tab-bookings"]').click(); await page.waitForTimeout(6000);
  out.tripsBookings = clean(await page.locator("body").innerText().catch(() => "")).slice(0, 320);
  await page.screenshot({ path: `${SHOTS}/lab_2_v2_trips_bookings.png`, fullPage: true }).catch(() => {});

  out.errors = errs.slice(0, 6); R.cases.push(out);
  console.log(JSON.stringify(out, null, 1));

  // C. desktop: Stay Explorer price honesty + route survival on reload
  const dctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "zh-CN" });
  const dp = await dctx.newPage();
  const derrs = []; attachErrors(dp, derrs);
  await dp.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(c.jid)});`);
  await dp.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await dp.waitForTimeout(5000);
  await dp.locator(".v8-nav button").filter({ hasText: "住宿选择" }).first().click();
  await dp.waitForTimeout(4000);
  const beforeReload = { path: new URL(dp.url()).pathname, stayExplorer: await dp.locator('[data-testid="v8-stay-explorer"]').count() };
  await dp.reload({ waitUntil: "domcontentloaded" }); await dp.waitForTimeout(8000);
  const afterReload = {
    path: new URL(dp.url()).pathname,
    stayExplorer: await dp.locator('[data-testid="v8-stay-explorer"]').count(),
    breadcrumb: clean(await dp.locator(".v8-breadcrumb").innerText().catch(() => "")),
    cards: await dp.locator('[data-testid="stay-offer-card"]').count(),
    priceUnknown: await dp.locator('[data-testid="stay-price-unknown"]').count(),
    priceKnown: await dp.locator('[data-testid="stay-price-known"]').count(),
    firstCard: clean(await dp.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => "")),
    detailTotal: clean(await dp.locator(".v8-detail-panel dd").nth(0).innerText().catch(() => "")),
    cancellation: clean(await dp.locator(".v8-detail-panel dd").nth(2).innerText().catch(() => "")),
    bodyHasZeroYuan: /¥0\.00/.test(clean(await dp.locator("body").innerText().catch(() => ""))),
  };
  await dp.screenshot({ path: `${SHOTS}/lab_2_v2_stay_desktop.png`, fullPage: true }).catch(() => {});
  const outC = { case: "C-stay-explorer", beforeReload, afterReload, errors: derrs.slice(0, 5) };
  R.cases.push(outC); console.log(JSON.stringify(outC, null, 1));

  fs.writeFileSync(`${EV}/cycle2_full.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

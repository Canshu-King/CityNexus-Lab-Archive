/** CYCLE 2 final verification (post-fix) on a fresh journey + a fresh DB. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreate, wizardCreateWithOptions, BASE, EV, SHOTS, fs } = L;
const R = { cases: [], errors: [] };
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const browser = await launch();

  // ---------- A. no journey at all ----------
  {
    const ctx = await context(browser); const page = await ctx.newPage();
    const errs = []; attachErrors(page, errs);
    const out = { case: "A-no-journey", routes: {} };
    for (const route of ["/", "/v8/hub", "/v8/trips", "/v8/live", "/v8/agent", "/v8/map", "/v8/me", "/v8/stay", "/v8/bookings", "/v8/authoritative", "/v8/studio", "/v8/discover", "/v8/intelligence", "/v8/twin"]) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" }); await page.waitForTimeout(2500);
      const body = clean(await page.locator("body").innerText().catch(() => ""));
      out.routes[route] = { len: body.length, blank: body.length < 10, setup: await page.locator('[data-testid="trial-setup"]').count(), text: body.slice(0, 80) };
    }
    out.blankRoutes = Object.entries(out.routes).filter(([, v]) => v.blank).map(([k]) => k);
    out.nonSetupRoutes = Object.entries(out.routes).filter(([, v]) => !v.setup).map(([k]) => k);
    out.errors = errs.slice(0, 5); R.cases.push(out);
    console.log("A: blank=", out.blankRoutes, "nonSetup=", out.nonSetupRoutes);
    await ctx.close();
  }

  // ---------- B. journey with no chosen plan ----------
  const ctx = await context(browser); const page = await ctx.newPage();
  const errs = []; attachErrors(page, errs);
  const c = await wizardCreateWithOptions(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
  R.jid = c.jid;
  const out = { case: "B-no-plan", jid: c.jid };
  const exp0 = (await api("GET", `/journeys/${c.jid}/experience`)).json;
  out.backend = { active_plan: exp0.active_plan, selected_option_id: exp0.selected_option_id, options: (exp0.options ?? []).length };
  console.log("B backend:", JSON.stringify(out.backend));

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.hub = {
    caveat: clean(await page.locator('[data-testid="hub-glance-caveat"]').innerText().catch(() => "")),
    glanceEmpty: await page.locator('[data-testid="hub-glance-empty"]').count(),
    stay: clean(await page.locator('[data-testid="today-stay"]').innerText().catch(() => "")),
    glanceRow: clean(await page.locator(".v8-day-row").innerText().catch(() => "")).slice(0, 150),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_final_hub_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.studio = {
    previewCaveat: clean(await page.locator('[data-testid="studio-preview-caveat"]').innerText().catch(() => "")),
    selectedStayBlock: await page.locator(".v8-selected-stay").count(),
    asideHeading: clean(await page.locator(".v8-aside-heading").innerText().catch(() => "")),
    stayTotal: clean(await page.locator('[data-testid="studio-stay-total"]').innerText().catch(() => "")),
    costLines: clean(await page.locator(".v8-cost-lines").innerText().catch(() => "")),
    feasibility: clean(await page.locator(".v8-feasibility").innerText().catch(() => "")),
    noPlanChecked: await page.locator('[data-testid="studio-no-plan"]').count(),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_final_studio_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-spend"]').click(); await page.waitForTimeout(6000);
  out.tripsSpend = { stayTotal: clean(await page.locator('[data-testid="spend-stay-total"]').innerText().catch(() => "")) };
  await page.screenshot({ path: `${SHOTS}/lab_2_final_trips_spend.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(9000);
  out.stayExplorer = {
    cards: await page.locator('[data-testid="stay-offer-card"]').count(),
    firstCard: clean(await page.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => "")),
    priceUnknown: await page.locator('[data-testid="stay-price-unknown"]').count(),
    priceKnown: await page.locator('[data-testid="stay-price-known"]').count(),
    cancellation: clean(await page.locator(".v8-detail-panel dd").nth(2).innerText().catch(() => "")),
    body: clean(await page.locator("body").innerText().catch(() => "")).slice(0, 400),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_final_stay_explorer.png`, fullPage: true }).catch(() => {});

  out.errors = errs.slice(0, 6); R.cases.push(out);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle2_final.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

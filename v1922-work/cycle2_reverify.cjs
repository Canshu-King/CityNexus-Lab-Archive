/** CYCLE 2 re-verification after the empty/degraded-state fixes. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreate, BASE, EV, SHOTS, fs } = L;
const R = { cases: [], errors: [] };
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const browser = await launch();

  // ---- A. no journey ----
  {
    const ctx = await context(browser); const page = await ctx.newPage();
    const errs = []; attachErrors(page, errs);
    const out = { case: "A-no-journey" };
    for (const route of ["/", "/v8/hub", "/v8/trips", "/v8/live", "/v8/agent", "/v8/map", "/v8/me", "/v8/stay", "/v8/bookings", "/v8/authoritative", "/v8/studio", "/v8/discover", "/v8/intelligence", "/v8/twin"]) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" }); await page.waitForTimeout(2500);
      const body = clean(await page.locator("body").innerText().catch(() => ""));
      out[route] = { len: body.length, blank: body.length < 10, setup: await page.locator('[data-testid="trial-setup"]').count(), text: body.slice(0, 90) };
    }
    out.errors = errs.slice(0, 5); R.cases.push(out); console.log("A ok, blank:", Object.entries(out).filter(([k, v]) => v && v.blank).map(([k]) => k));
    await ctx.close();
  }

  // ---- B. journey, no plan chosen ----
  const ctx = await context(browser); const page = await ctx.newPage();
  const errs = []; attachErrors(page, errs);
  const c = await wizardCreate(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
  R.jid = c.jid;
  const out = { case: "B-no-plan", jid: c.jid };

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.hub = {
    glanceCaveat: clean(await page.locator('[data-testid="hub-glance-caveat"]').innerText().catch(() => "")),
    glanceEmpty: await page.locator('[data-testid="hub-glance-empty"]').count(),
    stay: clean(await page.locator('[data-testid="today-stay"]').innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_R_hub_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(6000);
  out.studio = {
    previewCaveat: clean(await page.locator('[data-testid="studio-preview-caveat"]').innerText().catch(() => "")),
    selectedStay: clean(await page.locator(".v8-selected-stay").innerText().catch(() => "")),
    asideHeading: clean(await page.locator(".v8-aside-heading").innerText().catch(() => "")),
    costLines: clean(await page.locator(".v8-cost-lines").innerText().catch(() => "")),
    stayTotal: clean(await page.locator('[data-testid="studio-stay-total"]').innerText().catch(() => "")),
    feasibility: clean(await page.locator(".v8-feasibility").innerText().catch(() => "")),
    noPlanChecked: await page.locator('[data-testid="studio-no-plan"]').count(),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_R_studio_noplan.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(5000);
  await page.locator('[data-testid="trips-tab-spend"]').click(); await page.waitForTimeout(6000);
  out.tripsSpend = {
    stayTotal: clean(await page.locator('[data-testid="spend-stay-total"]').innerText().catch(() => "")),
    body: clean(await page.locator('[data-testid="trips-spend"]').innerText().catch(() => "")).slice(0, 260),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_R_trips_spend.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(8000);
  out.stayExplorer = {
    firstCard: clean(await page.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => "")),
    unknownBadges: await page.locator('[data-testid="stay-price-unknown"]').count(),
    knownBadges: await page.locator('[data-testid="stay-price-known"]').count(),
    cancellation: clean(await page.locator(".v8-detail-panel dd").nth(2).innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_2_R_stay_explorer.png`, fullPage: true }).catch(() => {});

  out.errors = errs.slice(0, 6);
  R.cases.push(out);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle2_reverify.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

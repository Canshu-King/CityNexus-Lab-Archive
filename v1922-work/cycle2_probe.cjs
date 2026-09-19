/** CYCLE 2 probe — empty / degraded states, no plan, no hotel, no booking. */
const L = require("./lab_lib.cjs");
const { launch, context, attachErrors, wizardCreate, BASE, EV, SHOTS, fs } = L;
const R = { runs: [], errors: [] };
const rec = (o) => { R.runs.push(o); console.log(JSON.stringify(o).slice(0, 400)); };
(async () => {
  const browser = await launch();

  // ---------- A. no journey at all ----------
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = []; attachErrors(page, errs);
    const out = { case: "A-no-journey" };
    for (const route of ["/", "/v8/hub", "/v8/trips", "/v8/live", "/v8/agent", "/v8/map", "/v8/me", "/v8/stay", "/v8/bookings", "/v8/authoritative", "/v8/studio", "/v8/discover", "/v8/intelligence", "/v8/twin"]) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);
      const body = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
      const blank = body.length < 10;
      const setup = await page.locator('[data-testid="trial-setup"]').count();
      out[route] = { len: body.length, blank, setup, text: body.slice(0, 150) };
      if (route === "/v8/trips") await page.screenshot({ path: `${SHOTS}/lab_2_A_trips_nojourney.png` }).catch(() => {});
    }
    out.errors = errs.slice(0, 6);
    rec(out);
    await ctx.close();
  }

  // ---------- B. journey exists, NO plan chosen ----------
  {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = []; attachErrors(page, errs);
    const c = await wizardCreate(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
    const out = { case: "B-no-plan", jid: c.jid };
    for (const route of ["/v8/hub", "/v8/trips", "/v8/live", "/v8/agent", "/v8/map", "/v8/me", "/v8/stay", "/v8/bookings", "/v8/authoritative", "/v8/studio", "/v8/twin"]) {
      await page.goto(BASE + route, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(4000);
      const body = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
      out[route] = { len: body.length, text: body.slice(0, 320) };
      await page.screenshot({ path: `${SHOTS}/lab_2_B_${route.replace(/\W/g, "_")}.png` }).catch(() => {});
    }
    // Trips sub-tabs
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
    for (const t of ["itinerary", "stay", "bookings", "spend"]) {
      await page.locator(`[data-testid="trips-tab-${t}"]`).click();
      await page.waitForTimeout(6000);
      out["trips-tab-" + t] = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").trim().slice(0, 340);
      await page.screenshot({ path: `${SHOTS}/lab_2_B_trips_${t}.png` }).catch(() => {});
    }
    out.errors = errs.slice(0, 8);
    rec(out);
    await ctx.close();
  }
  fs.writeFileSync(`${EV}/cycle2_probe.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); fs.writeFileSync(`${EV}/cycle2_probe.json`, JSON.stringify(R, null, 1), "utf8"); process.exit(1); });

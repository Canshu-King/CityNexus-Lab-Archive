/** CYCLE 1 re-verification after the wall-clock fix. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreate, runAiPlan, chooseFirstPlan, BASE, EV, SHOTS, fs } = L;
const R = { steps: [], errors: [] };
const step = (n, v) => { R.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 260) }); console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 170)); };
(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  attachErrors(page, R.errors);
  const txt = async (s) => page.locator(s).first().innerText().catch(() => "");
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_1_reverify_${n}.png` }).catch(() => {});

  const c = await wizardCreate(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
  R.jid = c.jid; step("create", c.jid);
  const ai = await runAiPlan(page, "第一次来厦门，想看海、老街和日落，不想太赶。");
  step("ai", `count=${ai.count}`);
  const cmp = await chooseFirstPlan(page);
  step("choose", `cards=${cmp.cards} chosen=${cmp.chosen}`);
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) { await page.waitForTimeout(5000); hotels = await page.locator('[data-testid="hotel-card"]').count(); if (hotels > 0) break; }
  let ok = false;
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click(); await page.waitForTimeout(5500);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) { ok = true; break; }
  }
  step("hotel", `cards=${hotels} chosen=${ok}`);
  if (!ok) throw new Error("no hotel");

  const e0 = (await api("GET", `/journeys/${c.jid}/experience`)).json;
  const s0 = (await api("GET", `/journeys/${c.jid}/stay-options`)).json;
  const base = { plan: e0.active_plan?.id, ids: (e0.active_plan?.activities ?? []).map((a) => a.id).join(","), stay: (s0.options ?? []).find((o) => o.status === "SELECTED")?.id };
  step("backend-base", `plan=${base.plan} n=${(e0.active_plan?.activities ?? []).length} stay=${base.stay}`);

  // consistency + refresh + back/forward
  const read = async () => ({
    todayWhen: (await txt('[data-testid="today-when"]')).trim(),
    todayStay: (await txt('[data-testid="today-stay"]')).trim(),
    todayNext: (await txt('[data-testid="today-next"]')).replace(/\n/g, " | ").trim().slice(0, 70),
    tripsStops: await page.locator('[data-testid="trip-stop"]').count(),
    firstStopClock: (await txt('[data-testid="trip-stop"]')).slice(0, 5),
    liveCurrent: (await txt('[data-testid="live-journey-current"]')).trim(),
    liveClock: (await txt('.v8-live-now strong')).trim(),
    hotelSel: await page.locator('[data-testid="hotel-chosen"]').count(),
  });
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(5000);
  const hub = await read(); step("hub", JSON.stringify(hub)); await shot("01_hub");
  await page.locator('[data-testid="nav-trips"]').click(); await page.waitForTimeout(3500);
  const trips = await read(); step("trips", JSON.stringify(trips)); await shot("02_trips");
  await page.locator('[data-testid="nav-hub"]').click(); await page.waitForTimeout(2500);
  await page.locator('[data-testid="nav-map"]').click(); await page.waitForTimeout(4000);
  step("map", `panels=${await page.locator('[data-testid="v8-maplibre-panel"], [data-testid="v8-map-empty"]').count()}`);
  await page.locator('[data-testid="nav-hub"]').click(); await page.waitForTimeout(3000);
  step("hub-reentry", JSON.stringify(await read()));

  for (const [route, name] of [["/v8/trips", "trips"], ["/v8/hub", "hub"], ["/v8/live", "live"]]) {
    await page.goto(BASE + route, { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4500);
    const before = await read();
    await page.reload({ waitUntil: "domcontentloaded" }); await page.waitForTimeout(6500);
    const after = await read();
    step(`refresh-${name}`, `before=${JSON.stringify(before)} after=${JSON.stringify(after)}`);
    await shot(`03_refresh_${name}`);
  }
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3000);
  await page.locator('[data-testid="nav-trips"]').click(); await page.waitForTimeout(2500);
  await page.locator('[data-testid="nav-hub"]').click(); await page.waitForTimeout(2500);
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
  const hist = [];
  for (let i = 0; i < 3; i++) { await page.goBack(); await page.waitForTimeout(2500); hist.push(await page.evaluate(() => location.pathname)); }
  for (let i = 0; i < 3; i++) { await page.goForward(); await page.waitForTimeout(2500); hist.push(await page.evaluate(() => location.pathname)); }
  step("back-forward", hist.join(" -> ")); await shot("04_backforward");

  const e1 = (await api("GET", `/journeys/${c.jid}/experience`)).json;
  const s1 = (await api("GET", `/journeys/${c.jid}/stay-options`)).json;
  const aft = { plan: e1.active_plan?.id, ids: (e1.active_plan?.activities ?? []).map((a) => a.id).join(","), stay: (s1.options ?? []).find((o) => o.status === "SELECTED")?.id };
  step("backend-after", `plan=${aft.plan} n=${(e1.active_plan?.activities ?? []).length} stay=${aft.stay}`);
  step("integrity", `planSame=${base.plan === aft.plan} stopsSame=${base.ids === aft.ids} staySame=${base.stay === aft.stay}`);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(5000);
  step("clock-consistency-final", JSON.stringify(await read()));
  await shot("05_final_hub");
  fs.writeFileSync(`${EV}/cycle1_reverify.json`, JSON.stringify(R, null, 1), "utf8");
  console.log("ERRORS", R.errors.length, R.errors.slice(0, 4));
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); R.failure = e.message; fs.writeFileSync(`${EV}/cycle1_reverify.json`, JSON.stringify(R, null, 1), "utf8"); process.exit(1); });

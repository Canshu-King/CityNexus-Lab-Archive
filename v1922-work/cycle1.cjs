/** CYCLE 1 — state integrity across reload / navigation / back-forward. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreate, runAiPlan, chooseFirstPlan, BASE, EV, SHOTS, fs } = L;
const R = { cycle: 1, hypothesis: "chosen plan + hotel survive hard refresh, browser back/forward and tab re-entry with no stale/contradictory readings across Today/Trips/Live/backend", steps: [], errors: [] };
const step = (name, value) => { R.steps.push({ name, value: String(value).replace(/\s+/g, " ").slice(0, 300) }); console.log(name, "=>", String(value).replace(/\s+/g, " ").slice(0, 160)); };

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  attachErrors(page, R.errors);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_1_${n}.png` }).catch(() => {});
  const txt = async (sel) => page.locator(sel).first().innerText().catch(() => "");

  // ---- create + plan + choose + hotel ----
  const created = await wizardCreate(page, { city: "厦门", budget: 3000, stayBudget: 1000 });
  R.jid = created.jid;
  step("wizard-create", `jid=${created.jid} inferred="${created.inferred}"`);
  if (!created.jid) throw new Error("no journey");

  const ai = await runAiPlan(page, "第一次来厦门，想看海、老街和日落，不想太赶。");
  step("ai-plan", `plan_count=${ai.count} text="${ai.text.slice(0, 90)}"`);
  const cmp = await chooseFirstPlan(page);
  step("choose-plan", `cards=${cmp.cards} chosen=${cmp.chosen} bands=${cmp.bands.join("/")}`);
  await shot("01_today_after_choose");

  // hotel
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 50; i++) { await page.waitForTimeout(3000); hotels = await page.locator('[data-testid="hotel-card"]').count(); if (hotels > 0) break; }
  let hotelOk = false, hotelErr = "", hotelName = "";
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(5500);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) { hotelOk = true; hotelName = await txt(`[data-testid="hotel-name"] >> nth=${i}`); break; }
    hotelErr = await txt('[data-testid="hotel-error"]');
  }
  step("choose-hotel", `cards=${hotels} chosen=${hotelOk} name="${hotelName}" err="${hotelErr}"`);
  await shot("02_hotel_chosen");
  if (!hotelOk) throw new Error("no hotel selectable");

  // ---- backend truth baseline ----
  const exp0 = (await api("GET", `/journeys/${created.jid}/experience`)).json;
  const stays0 = (await api("GET", `/journeys/${created.jid}/stay-options`)).json;
  const baseline = {
    active_plan: exp0.active_plan?.id,
    activities: (exp0.active_plan?.activities ?? []).length,
    activity_ids: (exp0.active_plan?.activities ?? []).map((a) => a.id).join(","),
    selected_stay: exp0.selected_option_id,
    stay_selected: (stays0.options ?? []).find((o) => o.status === "SELECTED")?.id,
    stay_name: (stays0.options ?? []).find((o) => o.status === "SELECTED")?.stay?.property_name,
  };
  R.baseline = baseline;
  step("backend-baseline", JSON.stringify(baseline).slice(0, 280));

  const readUi = async () => ({
    today_stay: (await txt('[data-testid="today-stay"]')).trim(),
    today_next: (await txt('[data-testid="today-next"]')).trim().slice(0, 80),
    trips_stops: await page.locator('[data-testid="trip-stop"]').count(),
    live_current: (await txt('[data-testid="live-journey-current"]')).trim(),
    hotel_selected: await page.locator('[data-testid="hotel-chosen"]').count(),
  });

  // ---- surface-by-surface consistency (no reload) ----
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  const hub = await readUi(); step("hub-read", JSON.stringify(hub));
  await shot("03_hub");
  await page.locator('[data-testid="nav-trips"]').click(); await page.waitForTimeout(3000);
  const trips = await readUi(); step("trips-read", JSON.stringify(trips));
  await page.locator('[data-testid="trips-tab-stay"]').click(); await page.waitForTimeout(6000);
  const tripsStay = await readUi(); step("trips-stay-read", JSON.stringify(tripsStay));
  await page.locator('[data-testid="nav-hub"]').click(); await page.waitForTimeout(2500);
  await page.locator('[data-testid="nav-map"]').click(); await page.waitForTimeout(4000);
  const mapHas = await page.locator('[data-testid="v8-maplibre-panel"], [data-testid="v8-map-empty"]').count();
  step("map-read", `panels=${mapHas}`);
  await page.locator('[data-testid="nav-hub"]').click(); await page.waitForTimeout(2500);
  const backHub = await readUi(); step("hub-reentry", JSON.stringify(backHub));

  // ---- hard refresh on three surfaces ----
  const refresh = async (route, name) => {
    await page.goto(BASE + route, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4500);
    const before = await readUi();
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const after = await readUi();
    step(`refresh-${name}`, `before=${JSON.stringify(before)} after=${JSON.stringify(after)}`);
    return { before, after };
  };
  const rTrips = await refresh("/v8/trips", "trips"); await shot("04_refresh_trips");
  const rHub = await refresh("/v8/hub", "hub"); await shot("05_refresh_hub");
  const rLive = await refresh("/v8/live", "live"); await shot("06_refresh_live");

  // ---- back / forward through a 4-deep history ----
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3000);
  await page.locator('[data-testid="nav-trips"]').click(); await page.waitForTimeout(2500);
  await page.locator('[data-testid="nav-live"]').click().catch(async () => { await page.goto(BASE + "/v8/live"); }); await page.waitForTimeout(3000);
  const hist = [];
  for (let i = 0; i < 2; i++) { await page.goBack(); await page.waitForTimeout(2500); hist.push(await page.evaluate(() => location.pathname)); }
  for (let i = 0; i < 2; i++) { await page.goForward(); await page.waitForTimeout(2500); hist.push(await page.evaluate(() => location.pathname)); }
  step("back-forward", hist.join(" -> "));
  await shot("07_backforward");
  const afterBf = await readUi(); step("after-backforward", JSON.stringify(afterBf));

  // ---- backend truth after all of it ----
  const exp1 = (await api("GET", `/journeys/${created.jid}/experience`)).json;
  const stays1 = (await api("GET", `/journeys/${created.jid}/stay-options`)).json;
  const after = {
    active_plan: exp1.active_plan?.id,
    activities: (exp1.active_plan?.activities ?? []).length,
    activity_ids: (exp1.active_plan?.activities ?? []).map((a) => a.id).join(","),
    selected_stay: exp1.selected_option_id,
    stay_selected: (stays1.options ?? []).find((o) => o.status === "SELECTED")?.id,
  };
  R.after = after;
  step("backend-after", JSON.stringify(after).slice(0, 280));
  const same = JSON.stringify(baseline.activity_ids) === JSON.stringify(after.activity_ids)
    && baseline.selected_stay === after.selected_stay && baseline.stay_selected === after.stay_selected;
  step("verdict-inputs", `planSame=${baseline.active_plan === after.active_plan} stopsSame=${baseline.activity_ids === after.activity_ids} staySame=${baseline.stay_selected === after.stay_selected} => identical=${same}`);

  fs.writeFileSync(`${EV}/cycle1_result.json`, JSON.stringify(R, null, 1), "utf8");
  console.log("ERRORS", R.errors.length, R.errors.slice(0, 5));
  await browser.close();
})().catch(async (e) => {
  console.error("FAIL:", e.message);
  R.failure = e.message;
  fs.writeFileSync(`${EV}/cycle1_result.json`, JSON.stringify(R, null, 1), "utf8");
  process.exit(1);
});

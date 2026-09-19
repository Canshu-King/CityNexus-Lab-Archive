/**
 * CYCLE 4 clean test: ONE disruption -> proposal -> accept.
 * Does the handled disruption stop being presented as an open problem?
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const ms = (iso) => Date.parse(iso);

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_4c_${n}.png`, fullPage: true }).catch(() => {});
  const out = { steps: [], errors: [] };
  const step = (n, v) => {
    out.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 400) });
    console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 200));
  };
  const allText = async (sel) => {
    const n = await page.locator(sel).count();
    const vals = [];
    for (let i = 0; i < n; i++) vals.push(clean(await page.locator(sel).nth(i).innerText().catch(() => "")));
    return vals;
  };

  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
  const jid = c.jid;
  out.jid = jid;
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  step("1-ai", `plans=${ai.count}`);
  const cmp = await L.chooseFirstPlan(page);
  step("2-choose", `cards=${cmp.cards} chosen=${cmp.chosen}`);

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
  step("3-hotel", `cards=${hotels} pinned=${pinned}`);
  if (!pinned) throw new Error("no hotel");

  const before = (await api("GET", `/journeys/${jid}/experience`)).json;
  const bActs = before.active_plan.activities;
  out.before = {
    plan: before.active_plan.id,
    n: bActs.length,
    locked: bActs.filter((a) => a.locked).map((a) => `${a.title}@${a.start_at}`),
  };

  // ONE disruption, on a stop that yields a real proposal
  let propBody = null, target = null, eventId = null;
  for (const cand of bActs.filter((a) => !a.locked)) {
    const ev = await api("POST", `/journeys/${jid}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: cand.id,
      provenance: "USER_REPORTED", payload: { source: "traveller-report" },
    });
    const prop = await api("POST", `/journeys/${jid}/replans`, { trigger_event_id: ev.json?.id });
    if (prop.json?.id) { propBody = prop.json; target = cand; eventId = ev.json.id; break; }
  }
  if (!propBody) throw new Error("no proposal for any stop");
  step("4-disruption", `target=${target.title}@${target.start_at} preserved=${propBody.locked_commitments_preserved} removed=${(propBody.diff?.removed ?? []).length} added=${(propBody.diff?.added ?? []).length} moved=${(propBody.diff?.moved ?? []).length}`);
  out.eventId = eventId;
  out.proposalId = propBody.id;
  out.target = { title: target.title, at: target.start_at };

  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.liveBefore = {
    disruptions: await page.locator('[data-testid="live-disruption"]').count(),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    unchanged: await allText('[data-testid="live-unchanged"]'),
  };
  step("5-live-before", JSON.stringify(out.liveBefore));
  await shot("01_before_accept");

  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false, msg = "";
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(2000);
    msg = clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => ""));
    if (/\u5df2/.test(msg)) { accepted = true; break; }
    if (await page.locator('[data-testid="live-handled"]').count()) { accepted = true; break; }
  }
  step("6-accept", `accepted=${accepted} message="${msg}"`);
  await shot("02_after_accept_live");

  const after = (await api("GET", `/journeys/${jid}/experience`)).json;
  const aActs = after.active_plan.activities;
  out.after = {
    plan: after.active_plan.id,
    changed: before.active_plan.id !== after.active_plan.id,
    n: aActs.length,
    locked: aActs.filter((a) => a.locked).map((a) => `${a.title}@${a.start_at}`),
    disruptionsShown: (after.active_plan.disruptions ?? []).length,
  };
  const lockedBefore = out.before.locked.map((x) => `${x.split("@")[0]}@${ms(x.split("@")[1])}`).sort();
  const lockedAfter = out.after.locked.map((x) => `${x.split("@")[0]}@${ms(x.split("@")[1])}`).sort();
  step("7-locked", `lockedSame=${JSON.stringify(lockedBefore) === JSON.stringify(lockedAfter)} before=${lockedBefore.length} after=${lockedAfter.length} missing=${JSON.stringify(lockedBefore.filter((k) => !lockedAfter.includes(k)))}`);

  const events = (await api("GET", `/journeys/${jid}/events`)).json;
  out.events = (Array.isArray(events) ? events : []).map((e) => ({ type: e.event_type, status: e.status, affected: e.affected_activity_id, id: e.id }));
  step("8-events", JSON.stringify(out.events.map((e) => `${e.type}:${e.status}`)));

  // what the traveller sees AFTER accepting
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.hubAfter = {
    attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
    alerts: clean(await page.locator(".v8-alerts button").first().getAttribute("aria-label").catch(() => "")),
  };
  await shot("03_after_accept_hub");

  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.liveAfter = {
    disruptions: await page.locator('[data-testid="live-disruption"]').count(),
    disruptionText: clean(await page.locator('[data-testid="live-disruption"]').innerText().catch(() => "")),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    noProposal: clean(await page.locator('[data-testid="live-no-proposal"]').innerText().catch(() => "")),
    handled: await page.locator('[data-testid="live-handled"]').count(),
    handledText: clean(await page.locator('[data-testid="live-handled"]').innerText().catch(() => "")),
    message: clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => "")),
  };
  step("9-live-after", JSON.stringify(out.liveAfter));
  await shot("04_after_accept_live_again");

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const dayButtons = await page.locator('[data-testid="trip-day-strip"] button').count();
  let total = 0;
  const perDay = [];
  for (let i = 0; i < dayButtons; i++) {
    await page.locator('[data-testid="trip-day-strip"] button').nth(i).click();
    await page.waitForTimeout(900);
    const n = await page.locator('[data-testid="trip-stop"]').count();
    perDay.push(n);
    total += n;
  }
  out.trips = { perDay, totalStops: total, backendStops: aActs.length, protected: await page.locator('[data-testid="trip-stop-protected"]').count(), backendLocked: out.after.locked.length };
  step("10-trips-agreement", JSON.stringify(out.trips));
  await shot("05_trips_all_days");

  await page.goto(BASE + "/v8/map", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.map = { panel: await page.locator('[data-testid="v8-maplibre-panel"]').count(), canvas: await page.locator('[data-testid="v8-maplibre-panel"] canvas').count() };
  step("11-map", JSON.stringify(out.map));

  out.errors = errs.slice(0, 6);
  step("page-errors", `${out.errors.length} ${JSON.stringify(out.errors.slice(0, 3))}`);
  fs.writeFileSync(`${EV}/cycle4_clean.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  out.failure = e.message;
  fs.writeFileSync(`${EV}/cycle4_clean.json`, JSON.stringify(out, null, 1), "utf8");
  process.exit(1);
});

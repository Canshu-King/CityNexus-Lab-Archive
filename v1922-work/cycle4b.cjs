/**
 * CYCLE 4 agreement check, done correctly.
 *
 * The previous comparison compared raw ISO strings, so the same instant written
 * as +00:00 and +08:00 looked like a moved commitment.  Compare instants, and
 * read every element of a multi-match locator.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const t = (iso) => Date.parse(iso);

const snap = (exp) => {
  const acts = exp?.active_plan?.activities ?? [];
  return {
    planId: exp?.active_plan?.id ?? null,
    count: acts.length,
    ids: acts.map((a) => a.id),
    locked: acts.filter((a) => a.locked).map((a) => ({ title: a.title, at: a.start_at, ms: t(a.start_at) })),
    all: acts.map((a) => ({ title: a.title, at: a.start_at, ms: t(a.start_at), locked: a.locked })),
  };
};

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_4b_${n}.png`, fullPage: true }).catch(() => {});
  const out = { steps: [], errors: [] };
  const step = (n, v) => {
    out.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 400) });
    console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 190));
  };
  const allText = async (sel) => {
    const n = await page.locator(sel).count();
    const vals = [];
    for (let i = 0; i < n; i++) vals.push(clean(await page.locator(sel).nth(i).innerText().catch(() => "")));
    return vals;
  };

  // ---- build journey + plan + hotel through the UI ----
  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
  const jid = c.jid;
  out.jid = jid;
  step("1-journey", jid);
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  step("2-ai", `plans=${ai.count}`);
  const cmp = await L.chooseFirstPlan(page);
  step("3-choose", `cards=${cmp.cards} chosen=${cmp.chosen}`);

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) {
    await page.waitForTimeout(5000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  let hotelName = "", hotelOk = false;
  for (let i = 0; i < Math.min(hotels, 8); i++) {
    hotelName = clean(await page.locator('[data-testid="hotel-name"]').nth(i).innerText().catch(() => ""));
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(7000);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) { hotelOk = true; break; }
  }
  step("4-hotel", `cards=${hotels} chosen=${hotelOk} name=${hotelName}`);
  if (!hotelOk) throw new Error("no hotel pinned");

  const before = snap((await api("GET", `/journeys/${jid}/experience`)).json);
  out.before = { planId: before.planId, count: before.count, locked: before.locked.map((l) => `${l.title}@${l.at}`) };
  step("5-before", `plan=${before.planId} n=${before.count} locked=${before.locked.length}`);

  // ---- disruption + replan, trying each mutable stop ----
  out.attempts = [];
  let propBody = null, target = null;
  for (const cand of before.all.filter((a) => !a.locked)) {
    const act = (await api("GET", `/journeys/${jid}/experience`)).json.active_plan.activities.find((a) => a.title === cand.title && t(a.start_at) === cand.ms);
    if (!act) continue;
    const ev = await api("POST", `/journeys/${jid}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: act.id,
      provenance: "USER_REPORTED", payload: { source: "traveller-report" },
    });
    const prop = await api("POST", `/journeys/${jid}/replans`, { trigger_event_id: ev.json?.id });
    const body = prop.json ?? {};
    out.attempts.push({ target: act.title, at: act.start_at, status: prop.status, message: body.error?.message ?? "", id: body.id ?? null });
    step("6-attempt", `${act.title}@${act.start_at} -> ${prop.status} ${body.id ? "PROPOSAL" : (body.error?.message ?? "").slice(0, 120)}`);
    if (body.id) { propBody = body; target = act; break; }
  }
  if (!propBody) throw new Error("no proposal: " + JSON.stringify(out.attempts).slice(0, 300));
  out.proposalId = propBody.id;
  step("7-proposal", `preserved=${propBody.locked_commitments_preserved} removed=${(propBody.diff?.removed ?? []).length} added=${(propBody.diff?.added ?? []).length} moved=${(propBody.diff?.moved ?? []).length}`);

  // ---- the traveller sees the proposal on Live and accepts it ----
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const liveBefore = {
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    affected: await allText('[data-testid="live-affected"]'),
    unchanged: await allText('[data-testid="live-unchanged"]'),
    removed: await allText('[data-testid="live-diff-removed"]'),
    added: await allText('[data-testid="live-diff-added"]'),
    moved: await allText('[data-testid="live-diff-moved"]'),
    summaries: await allText('[data-testid="live-summary"]'),
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
  };
  out.liveBefore = liveBefore;
  step("8-live-proposal", JSON.stringify(liveBefore).slice(0, 380));
  await shot("01_live_proposal");
  if (!liveBefore.proposals) throw new Error("no proposal on Live");

  // the proposal the traveller accepts is the one the product offers first
  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false, msg = "";
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(2000);
    msg = clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => ""));
    if (/\u5df2|updated|applied/.test(msg)) { accepted = true; break; }
    if (await page.locator('[data-testid="live-handled"]').count()) { accepted = true; break; }
  }
  step("9-accept", `accepted=${accepted} message="${msg}"`);
  await shot("02_live_accepted");

  // ---- agreement: backend vs Trips vs Live vs map vs Today ----
  const afterExp = (await api("GET", `/journeys/${jid}/experience`)).json;
  const after = snap(afterExp);
  out.after = { planId: after.planId, count: after.count, locked: after.locked.map((l) => `${l.title}@${l.at}`) };
  const props = (await api("GET", `/journeys/${jid}/replans`)).json;
  const accRow = (Array.isArray(props) ? props : []).find((p) => p.id === out.proposalId);
  step("10-backend", `plan=${after.planId} changed=${before.planId !== after.planId} n=${after.count} acceptedStatus=${accRow?.status ?? "?"} lockedBefore=${before.locked.length} lockedAfter=${after.locked.length}`);

  // instant-level comparison, not string comparison
  const beforeLockedKeys = before.locked.map((l) => `${l.title}@${l.ms}`).sort();
  const afterLockedKeys = after.locked.map((l) => `${l.title}@${l.ms}`).sort();
  const lockedSame = JSON.stringify(beforeLockedKeys) === JSON.stringify(afterLockedKeys);
  const missingLocked = beforeLockedKeys.filter((k) => !afterLockedKeys.includes(k));
  const affectedKey = `${target.title}@${t(target.start_at)}`;
  const unaffectedBefore = before.all.map((a) => `${a.title}@${a.ms}`).filter((k) => k !== affectedKey).sort();
  const afterAll = after.all.map((a) => `${a.title}@${a.ms}`).sort();
  const unaffectedMoved = unaffectedBefore.filter((k) => !afterAll.includes(k));
  step("11-locked-check", `lockedSame=${lockedSame} missingLocked=${JSON.stringify(missingLocked)}`);
  step("12-unaffected-check", `unaffectedCount=${unaffectedBefore.length} movedOrDropped=${unaffectedMoved.length} sample=${JSON.stringify(unaffectedMoved.slice(0, 4))}`);

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const tripsStops = await page.locator('[data-testid="trip-stop"]').count();
  const tripsProtected = await page.locator('[data-testid="trip-stop-protected"]').count();
  const tripsText = await allText('[data-testid="trip-stop"]');
  await shot("03_trips_after");
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const liveAfter = {
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
    current: clean(await page.locator('[data-testid="live-journey-current"]').innerText().catch(() => "")),
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    handled: await page.locator('[data-testid="live-handled"]').count(),
  };
  await shot("04_live_after");
  await page.goto(BASE + "/v8/map", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const mapState = {
    panel: await page.locator('[data-testid="v8-maplibre-panel"]').count(),
    canvas: await page.locator('[data-testid="v8-maplibre-panel"] canvas').count(),
    empty: await page.locator('[data-testid="v8-map-empty"]').count(),
  };
  await shot("05_map_after");
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const hubAfter = {
    heading: clean(await page.locator('[data-testid="today-heading"]').innerText().catch(() => "")),
    next: clean(await page.locator('[data-testid="today-next"]').innerText().catch(() => "")),
    attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
  };
  await shot("06_hub_after");

  const backendTitles = (afterExp.active_plan?.activities ?? []).map((a) => String(a.title));
  const tripsTitles = tripsText.map((row) => row.split("\n").filter(Boolean)[2] ?? "");
  const missingOnTrips = backendTitles.filter((bt) => !tripsTitles.some((tt) => tt.includes(bt) || bt.includes(tt)));
  step("13-agreement", `tripsStops=${tripsStops} backendStops=${backendTitles.length} match=${tripsStops === backendTitles.length} protectedBadges=${tripsProtected} backendLocked=${after.locked.length} missingOnTrips=${JSON.stringify(missingOnTrips.slice(0, 5))}`);
  step("14-live-after", JSON.stringify(liveAfter));
  step("15-map-after", JSON.stringify(mapState));
  step("16-hub-after", JSON.stringify(hubAfter));

  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(8000);
  step("17-live-refresh", JSON.stringify({
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    handled: await page.locator('[data-testid="live-handled"]').count(),
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
  }));
  await shot("07_live_refresh");

  out.errors = errs.slice(0, 8);
  step("page-errors", `${out.errors.length} ${JSON.stringify(out.errors.slice(0, 4))}`);
  fs.writeFileSync(`${EV}/cycle4b.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  out.failure = e.message;
  fs.writeFileSync(`${EV}/cycle4b.json`, JSON.stringify(out, null, 1), "utf8");
  process.exit(1);
});


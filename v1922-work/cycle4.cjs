/** CYCLE 4 - cross-surface agreement after disruption + replan + accept. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const R = { steps: [], errors: [] };
const step = (n, v) => {
  R.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 380) });
  console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 175));
};
const clean = (s) => String(s).replace(/\s+/g, " ").trim();

/** Snapshot of the authoritative plan, used to prove nothing moved silently. */
const snap = (exp) => {
  const acts = exp?.active_plan?.activities ?? [];
  return {
    planId: exp?.active_plan?.id ?? null,
    count: acts.length,
    ids: acts.map((a) => a.id).join(","),
    locked: acts.filter((a) => a.locked).map((a) => `${a.title}@${a.start_at}`).sort().join(" | "),
    schedule: acts.map((a) => `${a.title}@${a.start_at}`).join(" | "),
  };
};

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  attachErrors(page, R.errors);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_4_${n}.png`, fullPage: true }).catch(() => {});

  // ---- build a real journey with a chosen plan + hotel ----
  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
  const jid = c.jid;
  R.jid = jid;
  step("1-journey", jid);
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  step("2-ai", `plans=${ai.count}`);
  const cmp = await L.chooseFirstPlan(page);
  step("3-choose-plan", `cards=${cmp.cards} chosen=${cmp.chosen} bands=${cmp.bands.join("/")}`);

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) {
    await page.waitForTimeout(5000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  let hotelOk = false;
  for (let i = 0; i < Math.min(hotels, 6); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(6000);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) { hotelOk = true; break; }
  }
  step("4-hotel", `cards=${hotels} chosen=${hotelOk}`);
  if (!hotelOk) throw new Error("no hotel could be selected");
  await shot("01_before_disruption");

  const before = snap((await api("GET", `/journeys/${jid}/experience`)).json);
  R.before = before;
  step("5-truth-before", `plan=${before.planId} n=${before.count} locked=${before.locked.split(" | ").filter(Boolean).length}`);


  // ---- raise a disruption on a mutable stop (the traveller cannot type this) ----
  const exp = (await api("GET", `/journeys/${jid}/experience`)).json;
  const acts = exp.active_plan.activities;
  const mutable =
    acts.find((a) => !a.locked && !/Check in|Check out|Overnight|\u673a\u573a|\u5317\u7ad9/.test(a.title)) ??
    acts.find((a) => !a.locked);
  if (!mutable) throw new Error("no mutable activity");
  R.target = { id: mutable.id, title: mutable.title, start_at: mutable.start_at, locked: mutable.locked };
  step("6-target", `${mutable.title} @${mutable.start_at} locked=${mutable.locked}`);
  // A disruption the traveller can actually raise must be able to produce a
  // governed proposal.  Try the mutable stops in order and record every refusal
  // so a systematic refusal is visible instead of hidden.
  R.replanAttempts = [];
  let prop = null, propBody = null, chosenTarget = null, evId = null;
  for (const cand of acts.filter((a) => !a.locked)) {
    const ev = await api("POST", `/journeys/${jid}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: cand.id,
      provenance: "USER_REPORTED", payload: { source: "traveller-report" },
    });
    const attempt = await api("POST", `/journeys/${jid}/replans`, { trigger_event_id: ev.json?.id });
    const ab = attempt.json ?? {};
    R.replanAttempts.push({
      target: cand.title, start: cand.start_at, eventStatus: ev.status,
      replanStatus: attempt.status, message: ab.error?.message ?? "",
      proposalId: ab.id ?? null,
    });
    step("8-replan-attempt", `${cand.title}@${cand.start_at} -> ${attempt.status} ${ab.id ? "PROPOSAL" : (ab.error?.message ?? "").slice(0, 150)}`);
    if (ab.id) { prop = attempt; propBody = ab; chosenTarget = cand; evId = ev.json?.id; break; }
  }
  if (!propBody?.id) throw new Error("no replan proposal for any mutable stop: " + JSON.stringify(R.replanAttempts).slice(0, 300));
  step("8-replan-proposal", `target=${chosenTarget.title} preserved=${propBody.locked_commitments_preserved} removed=${(propBody.diff?.removed ?? []).length} added=${(propBody.diff?.added ?? []).length} moved=${(propBody.diff?.moved ?? []).length}`);
  R.proposalId = propBody.id;
  R.preservedFlag = propBody.locked_commitments_preserved;
  const mutable2 = chosenTarget;

  // ---- the traveller sees and accepts it on Live ----
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const liveBefore = {
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    proposal: await page.locator('[data-testid="live-proposal"]').count(),
    affected: clean(await page.locator('[data-testid="live-affected"]').innerText().catch(() => "")),
    unchanged: clean(await page.locator('[data-testid="live-unchanged"]').innerText().catch(() => "")),
    removed: clean(await page.locator('[data-testid="live-diff-removed"]').innerText().catch(() => "")),
    added: clean(await page.locator('[data-testid="live-diff-added"]').innerText().catch(() => "")),
    moved: clean(await page.locator('[data-testid="live-diff-moved"]').innerText().catch(() => "")),
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
  };
  R.liveBefore = liveBefore;
  step("9-live-proposal", JSON.stringify(liveBefore));
  await shot("02_live_proposal");
  if (!liveBefore.proposal) throw new Error("proposal not visible on Live");

  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false, msg = "";
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(2000);
    msg = clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => ""));
    if (/\u5df2|updated|applied/.test(msg)) { accepted = true; break; }
    if (await page.locator('[data-testid="live-handled"]').count()) { accepted = true; break; }
  }
  step("10-accept", `accepted=${accepted} message="${msg}"`);
  await shot("03_live_accepted");

  // ---- triple agreement: backend / Trips / Live / map / Today ----
  const afterExp = (await api("GET", `/journeys/${jid}/experience`)).json;
  const after = snap(afterExp);
  R.after = after;
  const acceptedProps = (await api("GET", `/journeys/${jid}/replans`)).json;
  const accRow = (Array.isArray(acceptedProps) ? acceptedProps : []).find((p) => p.id === R.proposalId);
  step("11-backend-after", `plan=${after.planId} n=${after.count} changedPlan=${before.planId !== after.planId} status=${accRow?.status ?? "?"} lockedBefore=${before.locked.split(" | ").filter(Boolean).length} lockedAfter=${after.locked.split(" | ").filter(Boolean).length}`);

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const tripsStops = await page.locator('[data-testid="trip-stop"]').count();
  const protectedCount = await page.locator('[data-testid="trip-stop-protected"]').count();
  await shot("04_trips_after");
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const liveAfter = {
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
    current: clean(await page.locator('[data-testid="live-journey-current"]').innerText().catch(() => "")),
    disruptionStill: await page.locator('[data-testid="live-disruption"]').count(),
    proposalStill: await page.locator('[data-testid="live-proposal"]').count(),
    handled: await page.locator('[data-testid="live-handled"]').count(),
  };
  await shot("05_live_after");
  await page.goto(BASE + "/v8/map", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const mapState = {
    panel: await page.locator('[data-testid="v8-maplibre-panel"]').count(),
    empty: await page.locator('[data-testid="v8-map-empty"]').count(),
    canvas: await page.locator('[data-testid="v8-maplibre-panel"] canvas').count(),
  };
  await shot("06_map_after");
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const hubAfter = {
    heading: clean(await page.locator('[data-testid="today-heading"]').innerText().catch(() => "")),
    next: clean(await page.locator('[data-testid="today-next"]').innerText().catch(() => "")),
    attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
  };
  await shot("07_hub_after");

  const backendTitles = (afterExp.active_plan?.activities ?? []).map((a) => String(a.title));
  const tripsAgree = tripsStops === backendTitles.length;
  const lockedPreserved = before.locked === after.locked;
  const noSilentMove = before.locked.split(" | ").filter(Boolean).every((l) => after.locked.includes(l));
  const unaffectedKept = before.schedule.split(" | ").filter((row) => !row.startsWith(mutable2.title)).every((row) => after.schedule.includes(row));
  step("12-agreement", `tripsStops=${tripsStops} backendStops=${backendTitles.length} tripsAgree=${tripsAgree} lockedPreserved=${lockedPreserved} noSilentMove=${noSilentMove} unaffectedKept=${unaffectedKept} protectedBadges=${protectedCount}`);
  step("13-live-after", JSON.stringify(liveAfter));
  step("14-map-after", JSON.stringify(mapState));
  step("15-hub-after", JSON.stringify(hubAfter));
  step("16-schedule", `before="${before.schedule.slice(0, 170)}" after="${after.schedule.slice(0, 170)}"`);

  // hard refresh must not re-introduce an accepted proposal
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  step("17-live-after-refresh", JSON.stringify({
    proposal: await page.locator('[data-testid="live-proposal"]').count(),
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    handled: await page.locator('[data-testid="live-handled"]').count(),
    next: clean(await page.locator('[data-testid="live-next"]').innerText().catch(() => "")),
  }));
  await shot("08_live_refresh");

  step("page-errors", `${R.errors.length} ${JSON.stringify(R.errors.slice(0, 5))}`);
  fs.writeFileSync(`${EV}/cycle4.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  R.failure = e.message;
  fs.writeFileSync(`${EV}/cycle4.json`, JSON.stringify(R, null, 1), "utf8");
  process.exit(1);
});


/**
 * FINAL v2 same-Xiamen trace.
 *
 * NEW hard requirement: a booking must be imported AND confirmed BEFORE the
 * closure/replan step, so the booking-first false-protected path is exercised.
 * Every replan identity is captured at ID level.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/final_v2";
fs.mkdirSync(SHOTS, { recursive: true });
const api = async (method, p, body) => {
  const r = await fetch(API + p, {
    method,
    headers: { "Content-Type": "application/json", "Idempotency-Key": `v2-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let j = null; try { j = JSON.parse(t); } catch { j = { _raw: t.slice(0, 260) }; }
  return { status: r.status, json: j };
};

const asArray = (value) => (Array.isArray(value) ? value : []);
const planIdsOf = (resp) => asArray(resp && resp.json).map((p) => p && p.id).filter(Boolean);

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({
    viewport: { width: 412, height: 915 }, deviceScaleFactor: 3.5,
    isMobile: true, hasTouch: true, locale: "zh-CN",
  });
  const page = await ctx.newPage();
  const errors = [];
  const T = [];
  let JID = null;
  const rec = (action, status, result, extra) =>
    T.push({ ts: new Date().toISOString(), journey_id: JID, action, status,
             result: String(result).replace(/\s+/g, " ").slice(0, 230), ...(extra || {}) });
  page.on("pageerror", (e) => errors.push(`pageerror:${String(e).slice(0, 150)}`));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|ERR_PROXY|AJAXError|Failed to load resource/.test(m.text()))
      errors.push(`console:${m.text().slice(0, 150)}`);
  });
  const shot = (n) => page.screenshot({ path: `${SHOTS}/${n}.png` }).catch(() => {});
  const has = async (s) => (await page.locator(s).count()) > 0;
  const txt = async (s) => page.locator(s).first().innerText().catch(() => "");

  const artifact = { run: "xiaomi-final-v2", started: new Date().toISOString(), journey_id: null, trace: T, errors, assertions: {} };

  try {
    // 1. create
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="trial-city"]').fill("厦门");
    await page.waitForTimeout(400);
    await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
    await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
    await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
    await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
    await page.locator('[data-testid="trial-budget"]').fill("3000");
    await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
    await page.locator('[data-testid="trial-create"]').click(); await page.waitForTimeout(9000);
    JID = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    artifact.journey_id = JID;
    rec("create-xiamen-journey", JID ? "201" : "NO-JOURNEY", JID || "");
    await shot("01_create");
    if (!JID) throw new Error("journey not created");

    // 2. AI plan, run-specific
    const before = await api("GET", `/journeys/${JID}/plans`);
    const baseline = planIdsOf(before);
    if (!Array.isArray(before.json)) {
      rec("baseline-warning", String(before.status), `non-array body: ${JSON.stringify(before.json).slice(0, 120)}`);
    }
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(() => {});
    await page.waitForTimeout(1200);
    await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
    await page.locator('[data-testid="plan-ai-submit"]').click();
    let reported = -1, newIds = [];
    for (let i = 0; i < 75; i++) {
      await page.waitForTimeout(2500);
      const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
      if (n !== null) {
        reported = Number(n);
        newIds = String(await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-new-plan-ids").catch(() => "") || "").split(",").filter(Boolean);
        break;
      }
    }
    const after = await api("GET", `/journeys/${JID}/plans`);
    const allPlans = asArray(after.json);
    const trulyNew = planIdsOf(after).filter((id) => !baseline.includes(id));
    if (!Array.isArray(after.json)) {
      rec("plans-warning", String(after.status), `non-array body: ${JSON.stringify(after.json).slice(0, 120)}`);
    }
    artifact.candidate_plan_ids = trulyNew;
    artifact.assertions.ai_run_specific = {
      baseline_count: baseline.length, reported_new_count: reported,
      reported_new_ids: newIds, backend_new_ids: trulyNew,
      old_plans_excluded: trulyNew.every((id) => !baseline.includes(id)),
      match: newIds.length === trulyNew.length && newIds.every((id) => trulyNew.includes(id)),
    };
    rec("ai-plan-run-specific", trulyNew.length >= 2 ? "new-candidates" : "no-new-candidates",
        `baseline=${baseline.length} new=${trulyNew.length} reported=${reported}`, { new_plan_ids: trulyNew });
    await shot("02_ai");
    await page.locator(".plan-ai-close").click().catch(() => {});
    await page.waitForTimeout(2000);
    if (trulyNew.length < 2) throw new Error("fewer than 2 new candidate plans");

    // 3. select
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await page.locator('[data-testid="plan-cmp-choose"]').first().click();
    for (let i = 0; i < 25; i++) {
      await page.waitForTimeout(2000);
      if (!(await has('[data-testid="plan-comparison"]'))) break;
    }
    const jSel = await api("GET", `/journeys/${JID}`);
    artifact.selected_plan_id = jSel.json?.active_plan_version_id ?? null;
    rec("select-plan", artifact.selected_plan_id ? "selected" : "not-selected", artifact.selected_plan_id || "",
        { selected_plan_id: artifact.selected_plan_id });
    if (!artifact.selected_plan_id) throw new Error("no active plan after selection");

    // 4. itinerary + detail
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    rec("trips-multiday", `${stops} stops`, "");
    await shot("03_trips");
    if (stops > 0) {
      await page.locator('[data-testid="trip-stop"]').first().click();
      await page.waitForTimeout(2000);
      rec("activity-detail", (await has('[data-testid="activity-detail"]')) ? "opened" : "MISSING", "");
      await shot("04_activity_detail");
      await page.locator('[data-testid="activity-back"]').click().catch(() => {});
      await page.waitForTimeout(1200);
    }

    // 5. hotel
    await page.waitForSelector('[data-testid="trips-tab-stay"]', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(3000);
    let hotels = 0;
    for (let attempt = 0; attempt < 3 && hotels === 0; attempt++) {
      await page.locator('[data-testid="trips-tab-stay"]').click().catch(() => {});
      for (let i = 0; i < 40; i++) {
        await page.waitForTimeout(3000);
        hotels = await page.locator('[data-testid="hotel-card"]').count();
        if (hotels > 0) break;
      }
    }
    let stayName = null;
    for (let i = 0; i < Math.min(hotels, 5); i++) {
      await page.locator('[data-testid="hotel-choose"]').nth(i).click();
      await page.waitForTimeout(5500);
      if (await has('[data-testid="hotel-chosen"]')) { stayName = (await txt('[data-testid="hotel-name"]')).trim(); break; }
    }
    rec("hotel-select", stayName ? "selected" : "not-selected", `${hotels} hotels | ${stayName || ""}`);
    await shot("05_hotel");
    if (!stayName) throw new Error("no hotel selected");

    // 6. booking import + CONFIRM  (must be BEFORE the closure step)
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="trips-tab-bookings"]').click();
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="inbox-tab-manual"]').click();
    await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("E2E-V2-BOOKING-1");
    await page.locator('[data-testid="manual-from"]').fill("厦门北站");
    await page.locator('[data-testid="manual-to"]').fill("深圳北站");
    await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    await page.locator('[data-testid="manual-submit"]').click();
    await page.waitForTimeout(7000);
    await page.locator('[data-testid="v13-2-anchor-role"]').selectOption("DEPARTURE").catch(() => {});
    await page.locator('[data-testid="v13-2-save-corrections"]').click().catch(() => {});
    await page.waitForTimeout(3500);
    await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
    await page.waitForTimeout(6000);
    let booking = null;
    for (let i = 0; i < 15; i++) {
      const w = await api("GET", `/journeys/${JID}/wallet`);
      booking = (w.json?.reservations || [])[0] || null;
      if (booking) break;
      await page.waitForTimeout(2000);
    }
    artifact.booking_id = booking?.id ?? null;
    artifact.assertions.booking_truth = {
      entity_set: "wallet.reservations",
      count: booking ? 1 : 0,
      booking_id: booking?.id ?? null,
      commitment_id: booking?.commitment_id ?? null,
      confirmation_ref: booking?.confirmation_ref ?? null,
      amount_minor: booking?.price?.amount_minor ?? null,
      amount_status: booking?.price?.status ?? null,
      origin: booking?.origin?.name ?? null,
      destination: booking?.destination?.name ?? null,
    };
    rec("booking-import-confirm", booking ? "confirmed" : "NOT-CONFIRMED",
        `ref=${booking?.confirmation_ref} amount=${booking?.price?.amount_minor} origin=${booking?.origin?.name}`,
        { booking_truth: artifact.assertions.booking_truth });
    await shot("06_booking");
    if (!booking) throw new Error("booking was not confirmed before the closure step");

    // Record the C4 commitments that exist at this point: this is the exact set
    // that used to make `None in {None}` falsely reject the closure.
    const commits = await api("GET", `/journeys/${JID}/wallet`);
    const c4 = (commits.json?.commitments || []);
    artifact.assertions.commitments_before_closure = c4.map((c) => ({
      id: c.id, level: c.level, activity_id: c.activity_id ?? null, external_ref: c.external_ref ?? null,
    }));
    rec("commitments-before-closure", `${c4.length} commitments`,
        `activity_id_nulls=${c4.filter((c) => (c.activity_id ?? null) === null).length}`,
        { commitments: artifact.assertions.commitments_before_closure });

    // 7. Copilot place question
    await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    if (!(await has('.cn-copilot-form textarea'))) {
      await page.locator('.cn-copilot-edge').click().catch(() => {});
      await page.waitForTimeout(1500);
    }
    let copilotAnswer = "";
    if (await has('.cn-copilot-form textarea')) {
      await page.locator('.cn-copilot-form textarea').fill("鼓浪屿好玩吗？");
      await page.locator('.cn-copilot-form button[type="submit"]').click();
      for (let i = 0; i < 40; i++) {
        await page.waitForTimeout(2500);
        if ((await page.locator('.cn-copilot-bubble.assistant').count()) > 0) {
          const last = await page.locator('.cn-copilot-bubble.assistant').last().innerText().catch(() => "");
          if (last.trim().length > 25) { copilotAnswer = last; break; }
        }
      }
    }
    const dockText = await txt('[data-testid="v18-copilot-dock"]');
    artifact.assertions.copilot = {
      question: "鼓浪屿好玩吗？",
      answer: copilotAnswer.slice(0, 400),
      answered: copilotAnswer.trim().length > 25,
      raw_vocabulary_leak: /DISCOVER|REQUEST_PLACE_SEARCH|EXPLAIN_PLAN|WHAT_IF|DeepSeek|Hermes|What-if Studio|JourneyTwin|deterministic/i.test(dockText),
    };
    rec("copilot-place-question", copilotAnswer.trim().length > 25 ? "answered" : "empty", copilotAnswer,
        { copilot: artifact.assertions.copilot });
    await shot("07_copilot");

    // 8. map + live
    await page.goto(BASE + "/v8/map", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4500);
    rec("xiamen-map", (await has('[data-testid="v8-maplibre-panel"]')) ? "panel" : "empty", "");
    await shot("08_map");
    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    rec("live", (await has('[data-testid="live-next"]')) ? "has-next" : "no-next", await txt('[data-testid="live-next"]'));
    await shot("09_live");

    // 9. ID-level "before" snapshot of the target
    const exp = await api("GET", `/journeys/${JID}/experience`);
    const plan = exp.json?.active_plan ?? {};
    const acts = plan.activities ?? [];
    const target = acts.find((a) => !a.locked);
    if (!target) throw new Error("no mutable stop to close");
    const targetPlace = target.place_id ?? null;
    const targetSemantic = (target.metadata || {}).semantic_key ?? null;
    artifact.assertions.replan_before = {
      journey_id: JID,
      base_plan_id: plan.id ?? null,
      affected_activity_id: target.id,
      affected_place_id: targetPlace,
      affected_semantic_key: targetSemantic,
      title: target.title,
      locked: Boolean(target.locked),
      activity_ids: acts.map((a) => a.id),
      place_ids: acts.map((a) => a.place_id ?? null),
    };
    rec("replan-before", "captured",
        `plan=${String(plan.id).slice(0, 8)} target=${String(target.title).slice(0, 22)} place=${String(targetPlace).slice(0, 20)}`,
        { replan_before: artifact.assertions.replan_before });

    // 10. explicit named mutable-POI closure
    const ev = await api("POST", `/journeys/${JID}/events`, {
      event_type: "CLOSURE", severity: "MAJOR",
      affected_activity_id: target.id,
      provenance: "USER_REPORTED",
      payload: { source: "traveller-report", named_venue: String(target.title) },
    });
    rec("closure-event", String(ev.status), `CLOSURE -> ${String(target.title).slice(0, 26)}`);
    const prop = await api("POST", `/journeys/${JID}/replans`, { trigger_event_id: ev.json?.id });
    const diff = prop.json?.diff ?? {};
    artifact.assertions.replan_proposal = {
      http: prop.status,
      proposal_id: prop.json?.id ?? null,
      proposed_plan_id: prop.json?.proposed_plan_version_id ?? null,
      status: prop.json?.status ?? null,
      locked_commitments_preserved: prop.json?.locked_commitments_preserved ?? null,
      removed: diff.removed ?? [],
      added: diff.added ?? [],
      moved: diff.moved ?? [],
      recovery_family: prop.json?.score_breakdown?.family ?? prop.json?.explanation?.family ?? null,
      error: prop.json?.error?.message ?? null,
    };
    rec("closure-proposal", String(prop.status),
        prop.json?.id
          ? `preserved=${prop.json?.locked_commitments_preserved} -${(diff.removed ?? []).length}/+${(diff.added ?? []).length}`
          : `NO PROPOSAL: ${prop.json?.error?.message ?? JSON.stringify(prop.json).slice(0, 120)}`,
        { replan_proposal: artifact.assertions.replan_proposal });
    await shot("10_live_proposal");

    // 11. accept through the UI (only if a proposal exists)
    if (prop.json?.id) {
      await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(6000);
      const cards = await page.locator('[data-testid="live-proposal"]').count();
      artifact.assertions.live_cards = {
        rendered_cards: cards,
        accept_buttons: await page.locator('[data-testid="live-accept"]').count(),
      };
      await shot("11_live_cards");
      await page.locator('[data-testid="live-accept"]').first().click();
      let accepted = false, msg = "";
      for (let i = 0; i < 25; i++) {
        await page.waitForTimeout(2000);
        msg = await txt('[data-testid="live-message"]');
        if (/已|updated/.test(msg)) { accepted = true; break; }
        if (await has('[data-testid="live-handled"]')) { accepted = true; break; }
      }
      rec("accept-replan", accepted ? "accepted" : "not-accepted", msg);
      await shot("12_live_accepted");
      artifact.assertions.accept = { accepted, message: msg };
    }

    // 12. ID-level "after" snapshot + contract assertions
    const post = await api("GET", `/journeys/${JID}/experience`);
    const postPlan = post.json?.active_plan ?? {};
    const postActs = postPlan.activities ?? [];
    const postIds = postActs.map((a) => a.id);
    // The experience payload exposes identity through metadata.semantic_key;
    // there is no top-level place_id.  Comparing `a.place_id ?? null` against a
    // targetPlace that is itself always null made this assertion "does any
    // activity have a null place_id", which is trivially true and hid a real
    // replan defect.  Compare the frozen identity the engine actually uses.
    //
    // X01 (non-degenerate criterion): a missing identity field must be reported
    // as UNKNOWN, never silently folded to null and then compared.  A null or
    // empty target semantic key would make `some(k => k === null)` match every
    // identity-less activity and turn this back into a tautology, so the run
    // records both endpoints and flags the degenerate case explicitly.
    const semOf = (a) => {
      const k = a && a.metadata ? a.metadata.semantic_key : null;
      return k === null || k === undefined || String(k).trim() === "" ? "UNKNOWN" : String(k);
    };
    const postSemanticKeys = postActs.map(semOf);
    const targetSemanticKnown =
      targetSemantic !== null && targetSemantic !== undefined && String(targetSemantic).trim() !== "";
    // Criterion under test: does the frozen identity of the closed venue still
    // appear among the post-accept activities?  Only meaningful when the left
    // endpoint is a real identity, hence `targetSemanticKnown`.  Extracted as a
    // pure function so its discrimination can be self-tested below.
    const closedVenueStillPresent = (keys, targetKey) => {
      const known =
        targetKey !== null && targetKey !== undefined && String(targetKey).trim() !== "";
      if (!known) return false;
      return keys.some((k) => k === String(targetKey));
    };
    const closedSemanticStillPresent = closedVenueStillPresent(postSemanticKeys, targetSemantic);
    const criterionNonDegenerate =
      targetSemanticKnown && postSemanticKeys.length > 0 && postSemanticKeys.some((k) => k !== "UNKNOWN");
    // X01/X03 self-test: prove the criterion is NOT a tautology by evaluating it
    // against synthetic inputs where the honest answer is false.  If none of
    // them can return false the predicate has lost its discriminating power.
    const criterionSelfTest = [
      { case: "closed venue still present", keys: ["a", String(targetSemantic ?? "t")], target: String(targetSemantic ?? "t"), expected: true },
      { case: "closed venue replaced", keys: ["a", "b"], target: String(targetSemantic ?? "t"), expected: false },
      { case: "all identities UNKNOWN", keys: ["UNKNOWN", "UNKNOWN"], target: String(targetSemantic ?? "t"), expected: false },
      { case: "empty activity set", keys: [], target: String(targetSemantic ?? "t"), expected: false },
      { case: "target identity UNKNOWN", keys: ["a", "UNKNOWN"], target: null, expected: false },
    ].map((t) => {
      const actual = closedVenueStillPresent(t.keys, t.target);
      return { ...t, actual, pass: actual === t.expected };
    });
    const criterionDiscriminates =
      criterionSelfTest.some((t) => t.actual === true) && criterionSelfTest.some((t) => t.actual === false);
    const planChanged = String(postPlan.id) !== String(plan.id);
    artifact.assertions.replan_after = {
      active_plan_id: postPlan.id ?? null,
      plan_changed: planChanged,
      activity_ids: postIds,
      place_ids: postActs.map((a) => (a.place_id ?? "UNKNOWN")),
      semantic_keys: postSemanticKeys,
      locked_before: acts.filter((a) => a.locked).length,
      locked_after: postActs.filter((a) => a.locked).length,
      locked_preserved: acts.filter((a) => a.locked).length === postActs.filter((a) => a.locked).length,
      closed_place_reappeared: closedSemanticStillPresent,
      closed_place_reappeared_checked_via: "metadata.semantic_key",
      closed_semantic_reappeared: closedSemanticStillPresent,
      closed_place_criterion: {
        expression: "postActs.some(a => a.metadata.semantic_key === affected_semantic_key)",
        left_operand: {
          name: "affected_semantic_key",
          value: targetSemanticKnown ? String(targetSemantic) : "UNKNOWN",
        },
        right_operand: { name: "post semantic_keys", value: postSemanticKeys },
        matches: postSemanticKeys.filter((k) => k === String(targetSemantic)),
        target_identity_known: targetSemanticKnown,
        non_degenerate: criterionNonDegenerate,
        discriminates: criterionDiscriminates,
        self_test: criterionSelfTest,
        // Criterion 2 ("the same closed Place cannot reappear through a new
        // Activity ID") only says something once a replacement was actually
        // applied.  If no proposal was accepted the active plan is untouched,
        // so the closed venue is still listed by definition and reading that as
        // a criterion-2 violation would be wrong.  Report applicability so the
        // boolean above is never read out of context.
        applicable: planChanged,
        applicability_reason: planChanged
          ? "a replan was accepted, so the post-accept activity set is the replacement result"
          : "no replan was accepted, so the active plan is unchanged and the closed venue is expected to remain",
        degenerate_reason: criterionNonDegenerate
          ? null
          : targetSemanticKnown
            ? "no post-accept activity carries a usable semantic_key"
            : "affected_semantic_key is UNKNOWN, so identity comparison would be tautological",
        // Why this is NOT always true: a successful replan replaces the closed
        // venue with a different semantic_key, and the matching activity id
        // changes too.  Recorded so a future regression back to a null-safe
        // tautology is visible.
        replacement_evidence: {
          before_activity_id: target.id,
          before_semantic_key: targetSemanticKnown ? String(targetSemantic) : "UNKNOWN",
          after_activity_ids: postIds,
          after_semantic_keys: postSemanticKeys,
          same_activity_id_survives: postIds.includes(target.id),
        },
      },
    };
    rec("replan-after", artifact.assertions.replan_after.plan_changed ? "plan-changed" : "unchanged",
        `active=${String(postPlan.id).slice(0, 8)} locked ${artifact.assertions.replan_after.locked_before}->${artifact.assertions.replan_after.locked_after} closedPlaceReappeared=${closedSemanticStillPresent} nonDegenerate=${criterionNonDegenerate}`,
        { replan_after: artifact.assertions.replan_after });

    // 13. Trips vs backend with a defined mapping
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const dayStripNav = page.locator('[data-testid="trip-day-strip"] button');
    const dayButtons = await dayStripNav.count();
    const uiTotal = [];
    for (let d = 0; d < Math.max(1, dayButtons); d++) {
      if (dayButtons > 0) { await dayStripNav.nth(d).click().catch(() => {}); await page.waitForTimeout(1500); }
      uiTotal.push(await page.locator('[data-testid="trip-stop"]').count());
    }
    const uiSum = uiTotal.reduce((a, b) => a + b, 0);
    artifact.assertions.triple_mapping = {
      entity_set: "Trips itinerary stop cards vs /experience active_plan.activities",
      ui_stops_per_day: uiTotal, ui_stops_total: uiSum, ui_day_buttons: dayButtons,
      backend_activities_total: postActs.length,
      expected: "equal because the itinerary lists every activity",
      comparison_valid: dayButtons > 0,
    };
    rec("trips-vs-backend", uiSum === postActs.length ? "match" : "differ",
        `ui=${uiSum} backend=${postActs.length}`, { triple_mapping: artifact.assertions.triple_mapping });
    await shot("13_trips_final");
  } catch (e) {
    rec("FAILURE", "error", e.message);
    artifact.failed = e.message;
  }

  artifact.finished = new Date().toISOString();
  fs.writeFileSync(`${EV}/VISIBLE_UI_TRACE_XIAOMI_FINAL.json`, JSON.stringify(artifact, null, 1), "utf8");
  fs.writeFileSync(`${EV}/REPLAN_IDENTITY_TRACE.json`, JSON.stringify({
    journey_id: artifact.journey_id,
    before: artifact.assertions.replan_before ?? null,
    proposal: artifact.assertions.replan_proposal ?? null,
    after: artifact.assertions.replan_after ?? null,
    live_cards: artifact.assertions.live_cards ?? null,
    accept: artifact.assertions.accept ?? null,
    booking: artifact.assertions.booking_truth ?? null,
    commitments_before_closure: artifact.assertions.commitments_before_closure ?? null,
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.action.padEnd(26)} ${String(t.status).padEnd(20)} ${t.result.slice(0, 76)}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})();

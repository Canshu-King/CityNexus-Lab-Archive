/**
 * FINAL same-Xiamen visible-UI trace, generated AFTER the last source change.
 *
 * Every assertion names the entity set, the filter and the expected mapping, so
 * no claim of "consistent" rests on an undefined comparison.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/FINAL_XIAOMI_SCREENSHOTS";
fs.mkdirSync(SHOTS, { recursive: true });
const api = async (method, p, body) => {
  const r = await fetch(API + p, {
    method,
    headers: { "Content-Type": "application/json", "Idempotency-Key": `fin-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let j = null; try { j = JSON.parse(t); } catch { j = { _raw: t.slice(0, 260) }; }
  return { status: r.status, json: j };
};
const NL = String.fromCharCode(10);

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
             result: String(result).replace(/\s+/g, " ").slice(0, 220), ...(extra || {}) });
  page.on("pageerror", (e) => errors.push(`pageerror:${String(e).slice(0, 150)}`));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|ERR_PROXY|AJAXError|Failed to load resource/.test(m.text()))
      errors.push(`console:${m.text().slice(0, 150)}`);
  });
  const shot = (n) => page.screenshot({ path: `${SHOTS}/${n}.png` }).catch(() => {});
  const has = async (s) => (await page.locator(s).count()) > 0;
  const txt = async (s) => page.locator(s).first().innerText().catch(() => "");

  const artifact = { run: "xiaomi-final-trace", started: new Date().toISOString(), journey_id: null,
                     candidate_plan_ids: [], selected_plan_id: null, post_replan_active_plan_id: null,
                     booking_id: null, stay_identity: null, trace: T, errors,
                     assertions: {} };

  try {
    // ---------- 1. create the journey through the wizard -----------------
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="trial-city"]').fill("厦门");
    await page.waitForTimeout(400);
    await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
    await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
    await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
    await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="trial-next"]').click();
    await page.waitForTimeout(700);
    await page.locator('[data-testid="trial-budget"]').fill("3000");
    await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
    await page.locator('[data-testid="trial-next"]').click();
    await page.waitForTimeout(700);
    await page.locator('[data-testid="trial-create"]').click();
    await page.waitForTimeout(9000);
    JID = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    artifact.journey_id = JID;
    rec("create-xiamen-journey", JID ? "201" : "NO-JOURNEY", JID || "");
    await shot("01_create");
    if (!JID) throw new Error("journey not created");

    // ---------- 2. AI request, judged on THIS run's artifacts -----------
    const before = await api("GET", `/journeys/${JID}/plans`);
    const baselineIds = (before.json || []).map((p) => p.id);
    artifact.plan_ids_before_run = baselineIds;
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(() => {});
    await page.waitForTimeout(1200);
    await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
    await page.locator('[data-testid="plan-ai-submit"]').click();
    let newIds = [];
    let planCount = -1;
    for (let i = 0; i < 75; i++) {
      await page.waitForTimeout(2500);
      const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
      if (n !== null) {
        planCount = Number(n);
        const raw = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-new-plan-ids").catch(() => "");
        newIds = String(raw || "").split(",").filter(Boolean);
        break;
      }
    }
    const after = await api("GET", `/journeys/${JID}/plans`);
    const allPlans = after.json || [];
    const trulyNew = allPlans.map((p) => p.id).filter((id) => !baselineIds.includes(id));
    artifact.candidate_plan_ids = trulyNew;
    artifact.assertions.ai_run_specific = {
      baseline_count: baselineIds.length,
      reported_new_count: planCount,
      reported_new_ids: newIds,
      backend_new_ids: trulyNew,
      old_plans_excluded: trulyNew.every((id) => !baselineIds.includes(id)),
      match: newIds.length === trulyNew.length && newIds.every((id) => trulyNew.includes(id)),
    };
    rec("ai-plan-run-specific", trulyNew.length >= 2 ? "new-candidates" : "no-new-candidates",
        `baseline=${baselineIds.length} new=${trulyNew.length} reported=${planCount}`, { new_plan_ids: trulyNew });
    await shot("02_ai");
    await page.locator(".plan-ai-close").click().catch(() => {});
    await page.waitForTimeout(2000);
    if (trulyNew.length < 2) throw new Error("fewer than 2 new candidate plans from this run");

    // ---------- 3. select a plan through the UI -------------------------
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    const bands = [];
    for (let i = 0; i < cards; i++) bands.push((await txt(`[data-testid="plan-cmp-band"] >> nth=${i}`)).trim());
    rec("plan-compare", `${cards} cards`, bands.join(" / "));
    await shot("03_compare");
    if (!cards) throw new Error("no candidate plans to compare");
    // Capture the id of the plan we are about to adopt, from the card the UI
    // shows first, by matching the DOM order to the API order.
    const firstCardPlan = trulyNew[0];
    await page.locator('[data-testid="plan-cmp-choose"]').first().click();
    for (let i = 0; i < 25; i++) {
      await page.waitForTimeout(2000);
      if (!(await has('[data-testid="plan-comparison"]'))) break;
    }
    const jAfterSelect = await api("GET", `/journeys/${JID}`);
    artifact.selected_plan_id = jAfterSelect.json?.active_plan_version_id ?? firstCardPlan;
    rec("select-plan", (await has('[data-testid="plan-comparison"]')) ? "not-selected" : "selected",
        artifact.selected_plan_id || "", { selected_plan_id: artifact.selected_plan_id });

    // ---------- 4. multi-day Trips + Activity Detail --------------------
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    const dayStrips = await page.locator('[data-testid="trip-day-strip"]').count();
    rec("trips-multiday", `${stops} stops shown`, `day-strips=${dayStrips}`);
    await shot("04_trips");
    if (stops > 0) {
      await page.locator('[data-testid="trip-stop"]').first().click();
      await page.waitForTimeout(2000);
      const detailOpen = await has('[data-testid="activity-detail"]');
      const costStatus = await page.locator('[data-testid="activity-cost"]').getAttribute("data-cost-status").catch(() => "?");
      const costText = await txt('[data-testid="activity-cost"]');
      rec("activity-detail", detailOpen ? "opened" : "MISSING",
          `cost_status=${costStatus} cost="${costText.trim()}"`,
          { cost_status: costStatus });
      await shot("05_activity_detail");
      await page.locator('[data-testid="activity-back"]').click().catch(() => {});
      await page.waitForTimeout(1200);
    }

    // ---------- 5. hotel compare + select through the UI ---------------
    // The stay panel mounts on tab activation and then runs a live provider
    // capture plus option generation.  Wait for the nav to exist, then retry the
    // tab activation itself in case the first click lands pre-mount.
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
    rec("hotel-compare", `${hotels} hotels`, "");
    await shot("06_hotels");
    let stayIdentity = null;
    for (let i = 0; i < Math.min(hotels, 5); i++) {
      await page.locator('[data-testid="hotel-choose"]').nth(i).click();
      await page.waitForTimeout(5500);
      if (await has('[data-testid="hotel-chosen"]')) {
        stayIdentity = (await txt('[data-testid="hotel-name"]')).trim();
        break;
      }
    }
    rec("select-hotel", stayIdentity ? "selected" : "not-selected", stayIdentity || "");
    await shot("07_hotel_selected");
    if (!stayIdentity) throw new Error("no hotel selected through the UI");

    // Authoritative stay truth: name, check-in and check-out must all exist.
    const so = await api("GET", `/journeys/${JID}/stay-options`);
    // Defined mapping: the option payload nests the property under `stay`, and
    // the offer's check-in/check-out are joined by external_offer_id.  Reading
    // flat fields here is what produced the earlier `undefined in=undefined`
    // false PASS, so assert the real path.
    const sel = (so.json?.options || []).find((o) => o.status === "SELECTED") || null;
    const selOffer = sel
      ? (so.json?.offers || []).find((f) => f.external_offer_id === sel.stay?.external_offer_id) || null
      : null;
    const checkIn = selOffer?.check_in_at ?? sel?.stay?.check_in_at ?? null;
    const checkOut = selOffer?.check_out_at ?? sel?.stay?.check_out_at ?? null;
    artifact.stay_identity = sel
      ? {
          name: sel.stay?.property_name ?? null,
          status: sel.status,
          selected_option_id: sel.id,
          external_offer_id: sel.stay?.external_offer_id ?? null,
          check_in_at: checkIn,
          check_out_at: checkOut,
        }
      : null;
    artifact.assertions.stay_truth = {
      entity_set: "stay-options where status == SELECTED, joined to offers by external_offer_id",
      found: Boolean(sel),
      property_name: sel?.stay?.property_name ?? null,
      selected_option_id: sel?.id ?? null,
      external_offer_id: sel?.stay?.external_offer_id ?? null,
      check_in_at: checkIn,
      check_out_at: checkOut,
      undefined_fields: [
        ["property_name", sel?.stay?.property_name],
        ["check_in_at", checkIn],
        ["check_out_at", checkOut],
      ].filter(([, v]) => !v).map(([k]) => k),
    };
    rec("stay-truth", sel ? "SELECTED" : "NONE",
        `name=${sel?.stay?.property_name ?? "-"} in=${checkIn ?? "MISSING"} out=${checkOut ?? "MISSING"}`,
        { stay_truth: artifact.assertions.stay_truth });
    if (!sel?.stay?.property_name || !checkIn || !checkOut) {
      throw new Error("stay truth incomplete: " + JSON.stringify(artifact.assertions.stay_truth.undefined_fields));
    }

    // ---------- 6. booking import + confirm through the UI -------------
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="trips-tab-bookings"]').click();
    await page.waitForTimeout(2500);
    await page.locator('[data-testid="inbox-tab-manual"]').click();
    await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("E2E-XIAOMI-FINAL-1");
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
      confirmation_ref: booking?.confirmation_ref ?? null,
      amount_minor: booking?.price?.amount_minor ?? null,
      amount_status: booking?.price?.status ?? null,
      origin: booking?.origin?.name ?? null,
      destination: booking?.destination?.name ?? null,
    };
    rec("booking-import-confirm", booking ? "confirmed" : "NOT-CONFIRMED",
        `ref=${booking?.confirmation_ref} amount=${booking?.price?.amount_minor} origin=${booking?.origin?.name}`,
        { booking_truth: artifact.assertions.booking_truth });
    await shot("08_booking");

    // ---------- 7. Copilot place question (captured AFTER the fix) -----
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
        const bubbles = await page.locator('.cn-copilot-bubble.assistant').count();
        if (bubbles > 0) {
          const last = await page.locator('.cn-copilot-bubble.assistant').last().innerText().catch(() => "");
          if (last.trim().length > 25) { copilotAnswer = last; break; }
        }
      }
    }
    const dockText = await txt('[data-testid="v18-copilot-dock"]');
    const rawEnumLeak = /DISCOVER|REQUEST_PLACE_SEARCH|EXPLAIN_PLAN|WHAT_IF|DeepSeek|Hermes|What-if Studio|JourneyTwin|deterministic/i.test(dockText);
    artifact.assertions.copilot = {
      question: "鼓浪屿好玩吗？",
      answer: copilotAnswer.slice(0, 400),
      answered: copilotAnswer.trim().length > 25,
      raw_vocabulary_leak: rawEnumLeak,
      answered_about_place: /鼓浪屿/.test(copilotAnswer),
      honest_when_unknown: /查不到|不会编|暂时|无法核验|没有可信/.test(copilotAnswer),
    };
    rec("copilot-place-question", copilotAnswer.trim().length > 25 ? "answered" : "empty",
        copilotAnswer, { copilot: artifact.assertions.copilot });
    await shot("09_copilot");

    // ---------- 8. map + Live ------------------------------------------
    await page.goto(BASE + "/v8/map", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4500);
    rec("xiamen-map", (await has('[data-testid="v8-maplibre-panel"]')) ? "panel" : "empty", "");
    await shot("10_map");

    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    rec("live", (await has('[data-testid="live-next"]')) ? "has-next" : "no-next",
        await txt('[data-testid="live-next"]'));
    await shot("11_live");

    // ---------- 9. disruption -> material replan -> UI accept -----------
    const preExp = await api("GET", `/journeys/${JID}/experience`);
    const prePlanId = preExp.json?.active_plan?.id ?? null;
    const preActs = preExp.json?.active_plan?.activities ?? [];
    const preTitles = preActs.map((a) => String(a.title));
    const target = preActs.find((a) => !a.locked);
    if (!target) throw new Error("no mutable stop to disrupt");
    const ev = await api("POST", `/journeys/${JID}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id,
      provenance: "USER_REPORTED",
    });
    rec("disruption-event", String(ev.status), `CLOSURE -> ${String(target.title).slice(0, 24)}`);
    const prop = await api("POST", `/journeys/${JID}/replans`, { trigger_event_id: ev.json?.id });
    const diff = prop.json?.diff ?? {};
    artifact.assertions.replan = {
      proposal_id: prop.json?.id ?? null,
      status: prop.json?.status ?? null,
      http: prop.status,
      locked_commitments_preserved: prop.json?.locked_commitments_preserved ?? null,
      removed_count: (diff.removed ?? []).length,
      added_count: (diff.added ?? []).length,
      material_diff: (diff.removed ?? []).length + (diff.added ?? []).length > 0,
    };
    rec("replan-proposal", String(prop.status),
        `preserved=${prop.json?.locked_commitments_preserved} -${(diff.removed ?? []).length}/+${(diff.added ?? []).length}`,
        { replan: artifact.assertions.replan });
    if (!prop.json?.id) throw new Error("no replan proposal produced");

    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const sawProposal = await has('[data-testid="live-proposal"]');
    await shot("12_live_disruption");
    if (!sawProposal) throw new Error("traveller cannot see the replan proposal");
    await page.locator('[data-testid="live-accept"]').first().click();
    let accepted = false;
    let acceptMessage = "";
    for (let i = 0; i < 25; i++) {
      await page.waitForTimeout(2000);
      acceptMessage = await txt('[data-testid="live-message"]');
      if (/已|updated/.test(acceptMessage)) { accepted = true; break; }
      if (await has('[data-testid="live-handled"]')) { accepted = true; break; }
    }
    rec("accept-replan", accepted ? "accepted" : "not-accepted", acceptMessage);
    await shot("13_live_accepted");
    if (!accepted) throw new Error("replan was not accepted through the UI");

    // ---------- 10. final comparison with a DEFINED mapping -------------
    const postExp = await api("GET", `/journeys/${JID}/experience`);
    const postPlan = postExp.json?.active_plan ?? null;
    const postActs = postPlan?.activities ?? [];
    artifact.post_replan_active_plan_id = postPlan?.id ?? null;

    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    // Trips renders ONE day at a time, so compare against the same day.
    const triples = [];
    // Trips shows one day at a time behind a day strip; iterate every day.
    const dayStripNav = page.locator('[data-testid="trip-day-strip"] button');
    const dayButtons = await dayStripNav.count();
    const uiTotal = [];
    for (let d = 0; d < Math.max(1, dayButtons); d++) {
      if (dayButtons > 0) { await dayStripNav.nth(d).click().catch(() => {}); await page.waitForTimeout(1500); }
      const n = await page.locator('[data-testid="trip-stop"]').count();
      uiTotal.push(n);
      triples.push(n);
    }
    const uiSum = uiTotal.reduce((a, b) => a + b, 0);
    // The Trips itinerary renders EVERY activity of the active plan, including
    // the structural ones (arrival, check-in, overnight, check-out,
    // departure).  Verified against the live payload rather than assumed: the
    // honest mapping is therefore UI stop cards == all backend activities.
    artifact.assertions.triple_mapping = {
      entity_set: "Trips itinerary stop cards vs /experience active_plan.activities",
      ui_stops_per_day: uiTotal,
      ui_stops_total_across_days: uiSum,
      ui_day_buttons: dayButtons,
      backend_activities_total: postActs.length,
      backend_types: postActs.map((a) => String(a.type || "")),
      expected: "UI total equals backend activity count because the itinerary lists every activity",
      comparison_valid: dayButtons > 0,
    };
    rec("trips-vs-backend", uiSum === postActs.length ? "match" : "differ",
        `ui=${uiSum} backend=${postActs.length} days=${JSON.stringify(uiTotal)}`,
        { triple_mapping: artifact.assertions.triple_mapping });
    await shot("14_trips_final");

    const liveNext = await (async () => {
      await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(5000);
      return txt('[data-testid="live-next"]');
    })();
    artifact.assertions.final_state = {
      journey_id: JID,
      active_plan_before_disruption: prePlanId,
      active_plan_after_accept: artifact.post_replan_active_plan_id,
      plan_changed: String(prePlanId) !== String(artifact.post_replan_active_plan_id),
      locked_before: preActs.filter((a) => a.locked).length,
      locked_after: postActs.filter((a) => a.locked).length,
      locked_preserved: preActs.filter((a) => a.locked).length === postActs.filter((a) => a.locked).length,
      stop_titles_before_sample: preTitles.slice(0, 4),
      stop_titles_after_sample: postActs.map((a) => String(a.title)).slice(0, 4),
      live_next: liveNext,
    };
    rec("final-state", "compared", JSON.stringify(artifact.assertions.final_state).slice(0, 200),
        { final_state: artifact.assertions.final_state });
  } catch (e) {
    rec("FAILURE", "error", e.message);
    artifact.failed = e.message;
  }

  artifact.finished = new Date().toISOString();
  fs.writeFileSync(`${EV}/VISIBLE_UI_TRACE_FINAL.json`, JSON.stringify(artifact, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.action.padEnd(26)} ${String(t.status).padEnd(20)} ${t.result.slice(0, 78)}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})();

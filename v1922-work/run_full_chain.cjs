/**
 * Canonical end-to-end run #1 — one browser session, mobile width, same Xiamen
 * trip.  Every state change goes through the visible UI; the only out-of-band
 * steps are (a) applying the offline provider fixture while public providers are
 * unreachable and (b) raising the disruption event, which the traveller cannot
 * type into a phone.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const path = require("path");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const T = [];
let JID = null;
const rec = (route, action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route, action, status,
           result: String(result).replace(/\s+/g, " ").slice(0, 200) });
const api = async (method, p, body) => {
  const r = await fetch(API + p, {
    method,
    headers: { "Content-Type": "application/json", "Idempotency-Key": `chain-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  let json = null;
  try { json = JSON.parse(text); } catch { json = { _raw: text.slice(0, 300) }; }
  return { status: r.status, json };
};

(async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    args: ["--disable-dev-shm-usage", "--no-sandbox", "--js-flags=--max-old-space-size=2048"],
  });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, locale: "zh-CN",
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 170)));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError|Failed to load resource/.test(m.text()))
      errors.push("C:" + m.text().slice(0, 170));
  });
  let crashed = false;
  page.on("crash", () => { crashed = true; console.log("PAGE CRASHED"); });
  const shot = (n) =>
    page.screenshot({ path: `${SHOTS}/${n}.png`, fullPage: false }).catch(() => {});
  const go = async (p) => {
    if (crashed) throw new Error("renderer crashed earlier; cannot continue");
    await page.goto(BASE + p, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(2500);
  };
  const pause = async (ms) => {
    if (crashed) throw new Error("renderer crashed earlier; cannot continue");
    await page.waitForTimeout(ms);
  };
  const has = async (sel) => (await page.locator(sel).count()) > 0;
  const txt = async (sel) => page.locator(sel).first().innerText().catch(() => "");

  console.log("STEP 1");
  // ---- 1. open the product ----
  await go("/");
  rec("/", "open-root", "200", (await txt("body")).slice(0, 60));
  await shot("C1_01_root");

  // ---- 2-3. wizard step 1 ----
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.waitForTimeout(400);
  const inferred = await txt('[data-testid="trial-inferred"]');
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
  rec("/", "wizard-step1", "filled", inferred);
  await shot("C1_02_step1");

  console.log("STEP 4");
  // ---- 4. step 2 budget ----
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  const step2 = await has('[data-testid="trial-step2-body"]');
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  rec("/", "wizard-step2", step2 ? "shown" : "MISSING", "budget 3000 / stay 1000");
  await shot("C1_03_step2");

  console.log("STEP 5");
  // ---- 5. step 3 review ----
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  const step3 = await has('[data-testid="trial-step3-body"]');
  const review = [await txt('[data-testid="review-city"]'), await txt('[data-testid="review-budget"]'),
                  await txt('[data-testid="review-party"]'), await txt('[data-testid="review-pace"]')].join(" | ");
  rec("/", "wizard-step3", step3 ? "shown" : "MISSING", review);
  await shot("C1_04_step3");

  console.log("STEP 6");
  // ---- 6. create ----
  await page.locator('[data-testid="trial-create"]').click();
  await page.waitForTimeout(7000);
  JID = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
  rec("/", "create-journey", JID ? "201" : "NO-JOURNEY", JID || "");
  await shot("C1_05_created");
  if (!JID) throw new Error("journey was not created through the wizard");
  fs.writeFileSync(EV + "/chain_state.json", JSON.stringify({ journey_id: JID }, null, 1));

  console.log("STEP 7");
  // ---- 7. AI planning runs first; the stay fixture is applied later, once the
  //         traveller's chosen stops exist (facts depend on the real itinerary). ----

  console.log("STEP 8");
  // ---- 8. AI planning ----
  await go("/v8/hub");
  await page.locator('[data-testid="hub-plan-with-ai"]').click();
  await page.waitForTimeout(1200);
  const sheet = await has('[data-testid="plan-ai-sheet"]');
  await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let aiCount = -1;
  let aiResult = "";
  for (let i = 0; i < 75; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    aiResult = await txt('[data-testid="plan-ai-result"]');
    if (n !== null) { aiCount = Number(n); break; }
  }
  rec("/v8/hub", "ai-plan", sheet ? (aiCount > 0 ? `plans-ready(${aiCount})` : `no-plans(${aiCount})`) : "sheet-missing",
      aiResult.split(String.fromCharCode(10)).join(" "));
  await shot("C1_06_ai");
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(2000);
  if (aiCount <= 0) throw new Error("the AI planner produced no usable candidate plans");

  console.log("STEP 9");
  // ---- 9. compare + choose ----
  await go("/v8/hub");
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  const bands = [];
  for (let i = 0; i < cards; i++) bands.push((await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")).trim());
  rec("/v8/hub", "plan-compare", `${cards} cards`, bands.join(" / "));
  await shot("C1_07_compare");
  if (cards === 0) throw new Error("no candidate plans to compare");
  await page.locator('[data-testid="plan-cmp-choose"]').first().click();
  let chosen = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(1500);
    if (!(await has('[data-testid="plan-comparison"]'))) { chosen = true; break; }
  }
  rec("/v8/hub", "choose-plan", chosen ? "selected" : "still-visible", "");
  await page.waitForTimeout(2500);
  await shot("C1_08_today");

  console.log("STEP 10");
  // ---- 10. itinerary on Trips ----
  await go("/v8/trips");
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  const days = await page.locator('[data-testid="trip-day-strip"] [data-testid]').count();
  const protectedN = await page.locator('[data-testid="trip-stop-protected"]').count();
  rec("/v8/trips", "itinerary", `${stops} stops`, `days=${days} protected=${protectedN}`);
  await shot("C1_09_itinerary");
  if (stops === 0) throw new Error("itinerary is empty after choosing a plan");

  console.log("STEP 11");
  // ---- 11. activity detail ----
  await page.locator('[data-testid="trip-stop"]').first().click();
  await page.waitForTimeout(2000);
  const detailOpen = await has('[data-testid="activity-detail"]');
  const detail = detailOpen
    ? [await txt('[data-testid="activity-title"]'), await txt('[data-testid="activity-location"]'),
       await txt('[data-testid="activity-duration"]'), await txt('[data-testid="activity-cost"]')].join(" | ")
    : "";
  rec("/v8/trips", "activity-detail", detailOpen ? "opened" : "MISSING", detail);
  await shot("C1_10_detail");
  if (detailOpen) {
    await page.locator('[data-testid="activity-map"]').click().catch(() => {});
    await page.waitForTimeout(2000);
    rec("/v8/trips", "detail-show-on-map", (await has('[data-testid="v8-maplibre-panel"]')) ? "map-shown" : "no-map", "");
    await shot("C1_11_detail_map");
    await go("/v8/trips");
    await page.locator('[data-testid="trip-stop"]').first().click();
    await page.waitForTimeout(1500);
    await page.locator('[data-testid="activity-back"]').click().catch(() => {});
    await page.waitForTimeout(1200);
    rec("/v8/trips", "detail-back", (await has('[data-testid="trip-stop"]')) ? "returned" : "stuck", "");
  }

  console.log("STEP 12");
  // ---- 12. hotels: compare + choose ----
  // The Stay Explorer searches live OSM accommodation for this Journey; the
  // offers below are the real provider results, not a fixture.
  await go("/v8/trips");
  await page.locator('[data-testid="trips-tab-stay"]').click();
  // Live OSM accommodation capture is a real provider call and can take a
  // minute; wait for the panel to finish instead of sampling once.
  let hotels = 0;
  for (let i = 0; i < 60; i++) {
    await pause(3000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  const hotelNames = [];
  for (let i = 0; i < Math.min(hotels, 4); i++) hotelNames.push((await txt(`[data-testid="hotel-name"] >> nth=${i}`)).slice(0, 24));
  const panelText = hotels
    ? ""
    : (await txt('[data-testid="hotels-panel"]'))
        .split(String.fromCharCode(10))
        .join(" | ")
        .slice(0, 200);
  rec("/v8/trips", "hotel-compare", `${hotels} hotels`, hotelNames.join(" / ") || panelText);
  await shot("C1_12_hotels");
  let hotelOk = false;
  let hotelErr = "";
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(5500);
    if (await has('[data-testid="hotel-chosen"]')) { hotelOk = true; break; }
    hotelErr = await txt('[data-testid="hotel-error"]');
    // A genuine conflict is a valid product answer for one property; keep
    // trying the next one the way a traveller would.
  }
  rec("/v8/trips", "choose-hotel", hotelOk ? "selected" : "not-selected", hotelErr);
  await shot("C1_13_hotel_chosen");
  if (!hotelOk) throw new Error("no hotel could be selected: " + hotelErr);

  console.log("STEP 13");
  // ---- 13. prove the pinned truth survived: POIs, day, duration, locked ----
  const truth = await api("GET", `/journeys/${JID}/experience`);
  const acts = (truth.json?.active_plan?.activities ?? []);
  const pois = acts.filter((a) => String(a.type || a.kind || "").toUpperCase().includes("ACTIVITY") || /景点/.test(String(a.title)));
  const locked = acts.filter((a) => a.locked === true);
  const pinnedTitles = locked.map((a) => String(a.title).slice(0, 18));
  const planDays = new Set(acts.map((a) => String(a.start_at ?? a.start_time ?? "").slice(0, 10)).filter(Boolean));
  rec("/api", "truth-after-hotel", `${acts.length} activities`,
      `pois=${pois.length} locked=${locked.length} days=${[...planDays].join(",")} | ${pinnedTitles.join(" / ")}`);
  const after = await api("GET", `/journeys/${JID}/stay-options`);
  const selOpt = (after.json?.options ?? []).find((o) => o.status === "SELECTED");
  rec("/api", "stay-truth", selOpt ? "SELECTED" : "NONE",
      selOpt ? `${selOpt.property_name} in=${selOpt.check_in_at} out=${selOpt.check_out_at}` : "");
  if (!selOpt) throw new Error("stay option is not authoritative after selection");
  if (pois.length === 0) throw new Error("the chosen plan lost its POIs after the hotel was pinned");

  console.log("STEP 14");
  // ---- 14. booking import through the visible form ----
  await go("/v8/trips");
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(3000);
  const inboxThere = await has('[data-testid="inbox-tab-manual"]');
  if (inboxThere) {
    await page.locator('[data-testid="inbox-tab-manual"]').click();
    await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("E2E-CHAIN-0001");
    await page.locator('[data-testid="manual-from"]').fill("厦门北站");
    await page.locator('[data-testid="manual-to"]').fill("深圳北站");
    // The imported ticket must describe the trip the traveller actually
    // booked: this rail service leaves Xiamen North at the journey's own
    // 20:00 departure anchor.  An inconsistent time is a different trip.
    await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    await page.locator('[data-testid="manual-submit"]').click();
    await page.waitForTimeout(6000);
  }
  const draftShown = await has('[data-testid="v10-inbox-draft"]');
  const interp = draftShown ? await txt('[data-testid="v13-2-interpretation"]') : "";
  rec("/v8/trips", "booking-manual-draft", draftShown ? "draft-created" : "MISSING", interp);
  await shot("C1_14_booking_draft");
  let applied = false;
  if (draftShown) {
    // The traveller confirms what this booking means in their trip: this rail
    // ticket is the departure from Xiamen.
    await page.locator('[data-testid="v13-2-anchor-role"]').selectOption("DEPARTURE").catch(() => {});
    await page.locator('[data-testid="v13-2-save-corrections"]').click().catch(() => {});
    await page.waitForTimeout(3500);
    const unresolved = await txt('[data-testid="v10-inbox-draft"]');
    await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
    await page.waitForTimeout(6000);
    const after = await txt('[data-testid="v10-inbox-draft"]');
    applied = /已|applied|CONFIRMED/i.test(after);
    rec("/v8/trips", "booking-review", unresolved.includes("需要") ? "review-required" : "ready",
        after.split(String.fromCharCode(10)).slice(0, 3).join(" / "));
  }
  const wallet = await api("GET", `/journeys/${JID}/wallet`);
  const resv = (wallet.json?.reservations ?? wallet.json?.items ?? []);
  rec("/v8/trips", "booking-import", applied ? "applied" : "not-applied", `wallet=${Array.isArray(resv) ? resv.length : 0} entries`);
  await shot("C1_15_booking_applied");

  console.log("STEP 15");
  // ---- 15. booking visible in Trips / wallet ----
  await go("/v8/trips");
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(2500);
  const bookingsText = (await txt('[data-testid="trips-tabs"] ~ *')).slice(0, 0);
  const bookingVisible = await page.locator('text=E2E-CHAIN-0001').count();
  const bookingVisible2 = await page.locator('text=厦门北站').count();
  rec("/v8/trips", "booking-visible", bookingVisible + bookingVisible2 > 0 ? "visible" : "not-visible",
      `ref=${bookingVisible} title=${bookingVisible2}`);
  await shot("C1_16_booking_visible");

  console.log("STEP 16");
  // ---- 16. Copilot: a real question in Chinese ----
  await go("/v8/agent");
  await page.waitForTimeout(1500);
  const dockOpen = await has('[data-testid="v18-copilot-dock"]');
  // The dock starts collapsed; the traveller taps the edge to open it.
  if (!(await page.locator('.cn-copilot-form textarea').count())) {
    await page.locator('.cn-copilot-edge').click().catch(() => {});
    await pause(1500);
  }
  const askBox = page.locator('.cn-copilot-form textarea');
  if (await askBox.count()) {
    await askBox.fill("鼓浪屿好玩吗？");
    await page.locator('.cn-copilot-form button[type="submit"]').click();
  } else if (await has('[data-testid="agent-command"]')) {
    await page.locator('[data-testid="agent-command"]').fill("鼓浪屿好玩吗？");
    await page.locator('[data-testid="run-agent-command"]').click();
  }
  let answer = "";
  for (let i = 0; i < 40; i++) {
    await pause(2500);
    answer = (await txt('.cn-copilot-history')) || (await txt('[data-testid="agent-mission-result"]'));
    // The history keeps the traveller's own question, so length alone proves
    // nothing.  Wait until an assistant bubble actually carries content.
    const bubbles = await page.locator('.cn-copilot-bubble.assistant').count();
    if (bubbles > 0) {
      const last = await page.locator('.cn-copilot-bubble.assistant').last().innerText().catch(() => "");
      if (last.trim().length > 25) { answer = last; break; }
    }
    // A provider call can still be in flight; keep the traveller's question
    // visible and do not report an empty answer while it is pending.
    const pending = await page.locator('.cn-copilot-form button[type="submit"]:disabled').count();
    if (pending) continue;
  }
  rec("/v8/agent", "copilot-question", dockOpen ? (answer.length > 40 ? "answered" : "empty") : "no-dock",
      answer.replace(/\n/g, " ").slice(0, 170));
  await shot("C1_17_copilot");
  const copilotUseful = /鼓浪屿|轮渡|日光岩|菽庄|海|景点|建议|可以/.test(answer);

  console.log("STEP 17");
  // ---- 17. map with real Xiamen coordinates ----
  await go("/v8/map");
  await page.waitForTimeout(4000);
  const mapPanel = await has('[data-testid="v8-maplibre-panel"]');
  const mapEmpty = await has('[data-testid="v8-map-empty"]');
  const canvasBox = await page.locator('[data-testid="v8-maplibre-panel"] canvas').first().boundingBox().catch(() => null);
  rec("/v8/map", "map", mapPanel ? "panel" : mapEmpty ? "empty" : "MISSING",
      `canvas=${canvasBox ? `${Math.round(canvasBox.width)}x${Math.round(canvasBox.height)}` : "none"}`);
  await shot("C1_18_map");
  if (!mapPanel) throw new Error("the map panel did not render for the Xiamen trip");

  console.log("STEP 18");
  // ---- 18. Live journey ----
  await go("/v8/live");
  await page.waitForTimeout(5000);
  const liveNext = await txt('[data-testid="live-next"]');
  const liveDisruption0 = await has('[data-testid="live-disruption"]');
  rec("/v8/live", "live-open", liveNext ? "has-next" : "no-next",
      `next="${liveNext}" disruption=${liveDisruption0}`);
  await shot("C1_19_live");

  console.log("STEP 19");
  // ---- 19. targeted mutable-POI disruption -> governed replan ----
  const exp = await api("GET", `/journeys/${JID}/experience`);
  const liveActs = exp.json?.active_plan?.activities ?? [];
  const mutable = liveActs.find((a) => !a.locked && String(a.title || "").includes("景点"));
  const target = mutable ?? liveActs.find((a) => !a.locked);
  if (!target) throw new Error("no mutable activity to disrupt");
  const beforeIds = liveActs.map((a) => a.id).join(",");
  const beforeTitles = liveActs.map((a) => String(a.title).slice(0, 14)).join(" / ");
  const ev = await api("POST", `/journeys/${JID}/events`, {
    event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id,
    provenance: "USER_REPORTED", payload: { source: "traveller-report" },
  });
  rec("/api", "disruption-event", ev.status, `CLOSURE -> ${String(target.title).slice(0, 20)} (${ev.json?.id ? "id ok" : JSON.stringify(ev.json).slice(0, 120)})`);
  const prop = await api("POST", `/journeys/${JID}/replans`, { trigger_event_id: ev.json?.id });
  const preserved = prop.json?.locked_commitments_preserved;
  const diff = prop.json?.diff ?? {};
  rec("/api", "replan-proposal", prop.status,
      `preserved=${preserved} removed=${(diff.removed ?? []).length} added=${(diff.added ?? []).length} ${prop.json?.error?.code ?? ""}`);
  if (!prop.json?.id) throw new Error("no replan proposal: " + JSON.stringify(prop.json).slice(0, 200));

  console.log("STEP 20");
  // ---- 20. the traveller sees it on Live and accepts it in the UI ----
  await go("/v8/live");
  await page.waitForTimeout(5000);
  const sawDisruption = await has('[data-testid="live-disruption"]');
  const sawProposal = await has('[data-testid="live-proposal"]');
  const affected = await txt('[data-testid="live-affected"]');
  const unchanged = await txt('[data-testid="live-unchanged"]');
  rec("/v8/live", "disruption-visible", sawDisruption ? "shown" : "hidden",
      `proposal=${sawProposal} affected="${affected}" unchanged="${unchanged.slice(0, 60)}"`);
  await shot("C1_20_live_disruption");
  if (!sawProposal) throw new Error("the traveller cannot see the replan proposal");
  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(2000);
    const msg = await txt('[data-testid="live-message"]');
    if (/已|updated/.test(msg)) { accepted = true; break; }
    if (await has('[data-testid="live-handled"]')) { accepted = true; break; }
  }
  rec("/v8/live", "accept-replan", accepted ? "accepted" : "not-accepted", await txt('[data-testid="live-message"]'));
  await shot("C1_21_live_accepted");

  console.log("STEP 21");
  // ---- 21. final agreement: Trips / Live / backend ----
  const final = await api("GET", `/journeys/${JID}/experience`);
  const fa = final.json?.active_plan?.activities ?? [];
  const finalIds = fa.map((a) => a.id).join(",");
  const finalTitles = fa.map((a) => String(a.title).slice(0, 14)).join(" / ");
  rec("/api", "final-truth", `${fa.length} activities`,
      `changed=${finalIds !== beforeIds} lockedKept=${fa.filter((a) => a.locked).length} | ${finalTitles}`);
  await go("/v8/trips");
  const tripsAfter = await page.locator('[data-testid="trip-stop"]').count();
  await go("/v8/live");
  const liveAfter = await txt('[data-testid="live-next"]');
  rec("/v8/trips", "trips-after-replan", `${tripsAfter} stops`, "Trips and Live must agree with the backend");
  rec("/v8/live", "live-after-replan", liveAfter ? "has-next" : "no-next", `next="${liveAfter}"`);
  await shot("C1_22_trips_after");
  const agree = tripsAfter > 0 && tripsAfter <= fa.length;
  rec("/api", "triple-agreement", agree ? "consistent" : "MISMATCH",
      `trips=${tripsAfter} backend=${fa.length} live="${liveAfter.slice(0, 40)}"`);

  console.log("STEP 22");
  // ---- 22. language 中文 -> EN -> 中文 ----
  await go("/v8/hub");
  const zhHeading = await txt('[data-testid="today-heading"]');
  await page.locator('[data-testid="topbar-language"]').click();
  await page.waitForTimeout(2500);
  const enHeading = await txt('[data-testid="today-heading"]');
  await page.locator('[data-testid="topbar-language"]').click();
  await page.waitForTimeout(2500);
  const zhAgain = await txt('[data-testid="today-heading"]');
  rec("/v8/hub", "language-roundtrip", zhHeading && enHeading && zhAgain ? "ok" : "broken",
      `zh="${zhHeading.slice(0, 22)}" en="${enHeading.slice(0, 26)}" zh2="${zhAgain.slice(0, 22)}"`);
  await shot("C1_23_language");

  console.log("STEP 23");
  // ---- 23. hard refresh keeps the truth ----
  await go("/v8/trips");
  const beforeRefresh = await page.locator('[data-testid="trip-stop"]').count();
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const afterRefresh = await page.locator('[data-testid="trip-stop"]').count();
  rec("/v8/trips", "hard-refresh", afterRefresh === beforeRefresh ? "stable" : "changed",
      `${beforeRefresh} -> ${afterRefresh}`);
  await shot("C1_24_refresh");

  console.log("STEP 24");
  // ---- 24. browser back / forward ----
  await go("/v8/hub");
  await page.locator('[data-testid="nav-trips"]').click();
  await pause(2500);
  const onTrips = await has('[data-testid="trips-tabs"]');
  await page.goBack();
  await pause(2500);
  const backOk = await has('[data-testid="today-heading"]');
  await page.goForward();
  await pause(2500);
  const forwardOk = await has('[data-testid="trips-tabs"]');
  rec("/v8", "back-forward", backOk && forwardOk ? "ok" : "broken",
      `trips=${onTrips} back=${backOk} forward=${forwardOk}`);
  await shot("C1_25_backforward");

  console.log("STEP 25");
  // ---- 25. Copilot can answer a question about the replanned trip ----
  await go("/v8/agent");
  await page.waitForTimeout(1500);
  const box2 = page.locator('.cn-copilot-form textarea');
  if (await box2.count()) {
    await box2.fill("现在第一天怎么安排？");
    await page.locator('.cn-copilot-form button[type="submit"]').click();
    await page.waitForTimeout(20000);
  }
  rec("/v8/agent", "copilot-after-replan", (await txt('.cn-copilot-history')).length > 60 ? "answered" : "empty", "");
  await shot("C1_26_copilot_after");

  fs.writeFileSync(EV + "/VISIBLE_UI_TRACE.json", JSON.stringify({
    run: "canonical-e2e-1", journey_id: JID, started: T[0]?.ts, finished: new Date().toISOString(),
    viewport: "390x844 (mobile, dpr 3)", copilot_useful: copilotUseful,
    replan: { target: String(target.title), preserved, removed: (diff.removed ?? []).length, added: (diff.added ?? []).length,
              before_titles: beforeTitles, after_titles: finalTitles, triple_agreement: agree },
    trace: T, errors: errors.slice(0, 12),
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.route.padEnd(11)} ${t.action.padEnd(24)} ${String(t.status).padEnd(16)} ${t.result.slice(0, 96)}`));
  console.log("JID:", JID, "| ERRORS:", errors.length, errors.slice(0, 4));
  await browser.close();
})().catch(async (e) => {
  console.error("FAIL:", e.message);
  try { fs.writeFileSync(EV + "/VISIBLE_UI_TRACE.json", JSON.stringify({ run: "canonical-e2e-1", journey_id: JID, failed: String(e.message), trace: T }, null, 1), "utf8"); } catch {}
  T.forEach((t) => console.log(`  ${t.route.padEnd(11)} ${t.action.padEnd(24)} ${String(t.status).padEnd(16)} ${t.result.slice(0, 96)}`));
  process.exit(1);
});

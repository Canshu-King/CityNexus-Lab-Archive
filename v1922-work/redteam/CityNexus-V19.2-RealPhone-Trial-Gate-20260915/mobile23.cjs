/**
 * V19.2.3 focused mobile trial probe.
 *
 * Viewports: 390x844 and 430x932 only.
 * Flows: ARRIVAL boundary, DEPARTURE boundary, mid-trip HARD recovery,
 * governed acknowledgement, feasible replacement resolves recovery,
 * no-alternative state, stale candidate warning, GPS allowed/denied.
 */

const { createRequire } = require("node:module");
const req = createRequire(
  "D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/snapshot_d/frontend/package.json",
);
const { chromium } = req("@playwright/test");
const fs = require("fs");

const BASE = process.env.WEB_BASE || "http://127.0.0.1:4214";
const API = process.env.API_BASE || "http://127.0.0.1:8000";
const OUT = process.env.OUT_PATH || "evidence/mobile_v1923_d.json";
const JID = "22222222-2222-4222-8222-222222222222";
const DAY = "2026-10-10";
const TZ = "+08:00";

async function api(path, init) {
  const response = await fetch(API + "/api/v1" + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  return { status: response.status, body };
}

function c4Reservation(role, ref, arrival, departure, node) {
  const reservation = {
    reservation_type: "RAIL",
    confirmation_ref: ref,
    origin: { name: "Shanghai Hongqiao", code: "SHH" },
    destination: { name: "Nexus City", code: "CNX" },
    scheduled_departure_at: departure,
    scheduled_arrival_at: arrival,
    anchor_role: role,
    provider_key: "mock-rail",
    price_amount_minor: 128000,
    currency: "CNY",
  };
  if (node) reservation.semantic_node_key = node;
  return reservation;
}

async function addAnchor(role, ref, arrival, departure, node) {
  const imported = await api(`/journeys/${JID}/inbox/import`, {
    method: "POST",
    body: JSON.stringify({
      artifact_type: "STRUCTURED_JSON",
      payload: { reservation: c4Reservation(role, ref, arrival, departure, node) },
    }),
  });
  const draftId = imported.body && imported.body.id;
  return draftId
    ? api(`/journeys/${JID}/inbox/${draftId}/confirm`, { method: "POST" })
    : { status: imported.status };
}

async function selectFirst() {
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (!list.length) return { list, select: { status: null }, start: { status: null } };
  const select = await api(`/journeys/${JID}/plans/${list[0].id}/select`, { method: "POST" });
  const start = await api(`/journeys/${JID}/start`, { method: "POST" });
  return { list, select, start };
}

async function openRoute(page, path) {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "citynexus.v8.journey_id",
      "22222222-2222-4222-8222-222222222222",
    );
  });
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(1600);
}

async function arrivalBoundaryFlow(vp, results) {
  await api("/demo/reset", { method: "POST" });
  const confirmed = await addAnchor(
    "ARRIVAL", `M23-A-${vp.name}`, `${DAY}T12:30:00${TZ}`, `${DAY}T08:00:00${TZ}`, null,
  );
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const plan = Array.isArray(plans.body) ? plans.body[0] : null;
  let boundaryOk = null;
  let anchorEnd = null;
  if (plan) {
    const anchor = plan.activities.find((a) => a.activity_type === "arrival");
    anchorEnd = anchor ? anchor.end_at : null;
    const flexible = plan.activities.filter((a) => a.activity_type !== "arrival");
    boundaryOk = flexible.length > 0 && flexible.every((a) => a.start_at >= anchor.end_at);
  }
  results.flows.push({
    viewport: vp.name,
    flow: "ARRIVAL_BOUNDARY",
    confirm: confirmed.status,
    generate: generated.status,
    plans: Array.isArray(plans.body) ? plans.body.length : 0,
    anchor_end: anchorEnd,
    no_flexible_before_arrival: boundaryOk,
  });
}

async function departureBoundaryFlow(vp, results) {
  await api("/demo/reset", { method: "POST" });
  const confirmed = await addAnchor(
    "DEPARTURE", `M23-D-${vp.name}`, `${DAY}T12:30:00${TZ}`, `${DAY}T15:30:00${TZ}`, null,
  );
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const plan = Array.isArray(plans.body) ? plans.body[0] : null;
  let boundaryOk = null;
  let anchorStart = null;
  if (plan) {
    const anchor = plan.activities.find((a) => a.activity_type === "departure");
    anchorStart = anchor ? anchor.start_at : null;
    const flexible = plan.activities.filter((a) => a.activity_type !== "departure");
    boundaryOk = flexible.length > 0 && flexible.every((a) => a.end_at <= anchor.start_at);
  }
  results.flows.push({
    viewport: vp.name,
    flow: "DEPARTURE_BOUNDARY",
    confirm: confirmed.status,
    generate: generated.status,
    plans: Array.isArray(plans.body) ? plans.body.length : 0,
    anchor_start: anchorStart,
    no_flexible_after_departure: boundaryOk,
  });
}

async function activeJourney() {
  await api("/demo/reset", { method: "POST" });
  await api(`/journeys/${JID}/plans/generate`, { method: "POST", body: JSON.stringify({}) });
  return selectFirst();
}

async function recoveryFlow(vp, page, results, pageErrors) {
  const picked = await activeJourney();
  const confirmed = await api(`/journeys/${JID}/capabilities/confirm`, {
    method: "POST",
    body: JSON.stringify([{ code: "STEP_FREE_REQUIRED", severity: "HARD", params: {} }]),
  });
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const title = visible
    ? await page.locator('[data-testid="recovery-required-title"]').innerText()
    : null;
  const ackButton = page.locator('[data-testid="recovery-acknowledge"]');
  const ackLabel = (await ackButton.count()) > 0 ? await ackButton.innerText() : null;
  results.flows.push({
    viewport: vp.name,
    flow: "MIDTRIP_HARD_RECOVERY",
    start_before: picked.start.status,
    confirm: confirmed.status,
    state: (confirmed.body && confirmed.body.recovery && confirmed.body.recovery.state) || null,
    experience_state:
      (experience.body && experience.body.recovery && experience.body.recovery.state) || null,
    ui_panel_visible: visible,
    ui_title: title,
    ui_acknowledge_label: ackLabel,
    ui_acknowledge_is_governed: ackLabel !== null && !/continue without/i.test(ackLabel),
    page_errors: pageErrors.slice(0, 3),
  });
  return picked;
}

async function acknowledgeFlow(vp, page, results, pageErrors) {
  const ackButton = page.locator('[data-testid="recovery-acknowledge"]');
  if ((await ackButton.count()) === 0) {
    results.flows.push({ viewport: vp.name, flow: "ACKNOWLEDGE_WARNING", skipped: true });
    return;
  }
  await ackButton.click();
  await page.waitForTimeout(1500);
  const stillVisible = (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const ackResponse = await api(`/journeys/${JID}/recovery/acknowledge`, { method: "POST" });
  const experience = await api(`/journeys/${JID}/experience`);
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "ACKNOWLEDGE_WARNING",
    backend_status: ackResponse.status,
    backend_resolved: ackResponse.body ? ackResponse.body.resolved : null,
    backend_acknowledged: ackResponse.body ? ackResponse.body.acknowledged : null,
    banner_still_visible: stillVisible,
    needs_review_after: flags.needs_review,
    recovery_required_after: flags.recovery_required,
    page_errors: pageErrors.slice(0, 3),
  });
}

async function noAlternativeFlow(vp, results) {
  const attempt = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const experience = await api(`/journeys/${JID}/experience`);
  const recovery = (experience.body && experience.body.recovery) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "NO_ALTERNATIVE",
    replan_status: attempt.status,
    state: recovery.state,
    replan_attempted: recovery.replan_attempted,
    no_alternative: recovery.no_alternative,
    needs_review: (experience.body && experience.body.experience_flags || {}).needs_review,
  });
}

async function replacementResolvesFlow(vp, page, results, pageErrors) {
  // Relax the HARD need, then generate + select a feasible replacement.
  await api(`/journeys/${JID}/capabilities`, { method: "PUT", body: JSON.stringify([]) });
  await api(`/journeys/${JID}/capabilities/confirm`, { method: "POST", body: JSON.stringify([]) });
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  let selected = { status: null };
  for (const plan of list) {
    const attempt = await api(`/journeys/${JID}/plans/${plan.id}/select`, { method: "POST" });
    if (attempt.status === 200) {
      selected = attempt;
      break;
    }
  }
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panelVisible =
    (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "FEASIBLE_REPLACEMENT_RESOLVES",
    generate: generated.status,
    select: selected.status,
    recovery_after: experience.body ? experience.body.recovery : null,
    needs_review_after: flags.needs_review,
    recovery_required_after: flags.recovery_required,
    panel_still_visible: panelVisible,
    page_errors: pageErrors.slice(0, 3),
  });
}

async function staleFlow(vp, page, results, pageErrors) {
  await api("/demo/reset", { method: "POST" });
  await api(`/journeys/${JID}/plans/generate`, { method: "POST", body: JSON.stringify({}) });
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (list.length) {
    await api(`/journeys/${JID}/plans/${list[0].id}/select`, { method: "POST" });
  }
  const { execFileSync } = require("node:child_process");
  try {
    execFileSync(
      process.env.LAB_PY || "D:/moodle/CityNexus/.venv/Scripts/python.exe",
      [process.env.EXPIRE_SCRIPT, list[0].id],
      { stdio: "pipe" },
    );
  } catch {
    // the stale assertions below still report the observed behaviour
  }
  const listed = await api(`/journeys/${JID}/plans`);
  const flagged = (Array.isArray(listed.body) ? listed.body : []).find(
    (p) => p.id === list[0].id,
  );
  const started = await api(`/journeys/${JID}/start`, { method: "POST" });
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panelVisible =
    (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "STALE_CANDIDATE_WARNING",
    candidate_flagged_stale: flagged ? flagged.stale : null,
    candidate_selectable: flagged ? flagged.selectable : null,
    start_status: started.status,
    start_message: String(
      (started.body && started.body.error && started.body.error.message) || "",
    ).slice(0, 120),
    journey_status: (await api(`/journeys/${JID}`)).body.status,
    flags_staleness: flags.staleness,
    panel_visible: panelVisible,
    page_errors: pageErrors.slice(0, 3),
  });
}

async function gpsFlow(browser, vp, results) {
  for (const gps of ["allowed", "denied"]) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      permissions: gps === "allowed" ? ["geolocation"] : [],
      geolocation: gps === "allowed" ? { latitude: 39.1, longitude: 117.18 } : undefined,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await openRoute(page, "/v8/live");
    const state = await page.evaluate(() => ({
      textLength: document.body ? document.body.innerText.length : 0,
      overflow:
        document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    }));
    results.flows.push({
      viewport: vp.name,
      flow: `GPS_${gps.toUpperCase()}`,
      rendered: state.textLength > 0,
      horizontal_overflow: state.overflow,
      page_errors: errors.slice(0, 3),
    });
    await context.close();
  }
}

async function main() {
  const results = { viewports: [], flows: [] };
  const browser = await chromium.launch({ channel: "chrome" });
  const VIEWPORTS = [
    { name: "390x844", width: 390, height: 844, mobile: true },
    { name: "430x932", width: 430, height: 932, mobile: true },
  ];
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(String(e)));
    page.on("console", (m) => {
      if (m.type() === "error") pageErrors.push(m.text());
    });

    await arrivalBoundaryFlow(vp, results);
    await departureBoundaryFlow(vp, results);
    await recoveryFlow(vp, page, results, pageErrors);
    await acknowledgeFlow(vp, page, results, pageErrors);
    await noAlternativeFlow(vp, results);
    await replacementResolvesFlow(vp, page, results, pageErrors);
    await staleFlow(vp, page, results, pageErrors);
    await gpsFlow(browser, vp, results);
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(OUT, JSON.stringify(results, null, 1));
  console.log(JSON.stringify(results, null, 1));
}

main().catch((error) => {
  console.error("PROBE_FAILED", error);
  process.exit(1);
});

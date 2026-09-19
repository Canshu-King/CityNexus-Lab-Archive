/**
 * V19.2.2 focused mobile trial probe.
 *
 * Two mandated viewports (390x844, 430x932) and the trial-critical flows:
 *   - C4 anchored journey
 *   - stale evidence warning
 *   - mid-trip HARD recovery panel
 *   - GPS allowed / denied
 *
 * Also asserts no horizontal overflow and no uncaught page errors.
 */

const { chromium } = require("playwright");
const fs = require("fs");

const BASE = process.env.WEB_BASE || "http://127.0.0.1:4214";
const API = process.env.API_BASE || "http://127.0.0.1:8070";
const OUT = process.env.OUT_PATH || "evidence/mobile_probe_d.json";

const VIEWPORTS = [
  { name: "390x844", width: 390, height: 844, mobile: true },
  { name: "430x932", width: 430, height: 932, mobile: true },
];

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

const resetDemo = () => api("/demo/reset", { method: "POST" });

function c4Reservation(ref) {
  return {
    reservation_type: "RAIL",
    confirmation_ref: ref,
    origin: { name: "Shanghai Hongqiao", code: "SHH" },
    destination: { name: "Nexus City", code: "CNX" },
    scheduled_departure_at: "2026-10-10T08:00:00+08:00",
    scheduled_arrival_at: "2026-10-10T12:30:00+08:00",
    anchor_role: "ARRIVAL",
    provider_key: "mock-rail",
    price_amount_minor: 128000,
    currency: "CNY",
  };
}

async function importAndConfirm(journeyId, reservation) {
  const imported = await api(`/journeys/${journeyId}/inbox/import`, {
    method: "POST",
    body: JSON.stringify({
      artifact_type: "STRUCTURED_JSON",
      payload: { reservation },
    }),
  });
  const draftId = imported.body && imported.body.id;
  const confirmed = draftId
    ? await api(`/journeys/${journeyId}/inbox/${draftId}/confirm`, {
        method: "POST",
      })
    : { status: null };
  return { imported, confirmed };
}

async function selectFirstPlan(journeyId) {
  const plans = await api(`/journeys/${journeyId}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (!list.length) return { plans, select: { status: null }, start: { status: null } };
  const select = await api(`/journeys/${journeyId}/plans/${list[0].id}/select`, {
    method: "POST",
  });
  const start = await api(`/journeys/${journeyId}/start`, { method: "POST" });
  return { plans, select, start, list };
}

async function c4Flow(browser, vp, results) {
  await resetDemo();
  const journeyId = "22222222-2222-4222-8222-222222222222";
  const { imported, confirmed } = await importAndConfirm(
    journeyId,
    c4Reservation(`MOBILE-C4-${vp.name}`),
  );
  const generated = await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  results.flows.push({
    viewport: vp.name,
    flow: "C4_ANCHORED_JOURNEY",
    import: imported.status,
    confirm: confirmed.status,
    generate: generated.status,
    plans: picked.list ? picked.list.length : 0,
    select: picked.select.status,
    start: picked.start.status,
  });
}

async function renderRoute(page, viewport, path, results, pageErrors) {
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(1200);
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    textLength: document.body ? document.body.innerText.length : 0,
  }));
  const panelCount = await page
    .locator('[data-testid="recovery-required-panel"]')
    .count();
  results.viewports.push({
    viewport,
    route: path,
    rendered: overflow.textLength > 0,
    horizontal_overflow: overflow.scrollWidth > overflow.clientWidth + 1,
    recovery_panel_present: panelCount > 0,
    page_errors: pageErrors.slice(0, 5),
  });
}

async function recoveryFlow(browser, vp, results, page, pageErrors) {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  const confirmed = await api(`/journeys/${journeyId}/capabilities/confirm`, {
    method: "POST",
    body: JSON.stringify([
      { code: "STEP_FREE_REQUIRED", severity: "HARD", params: {} },
    ]),
  });
  const experience = await api(`/journeys/${journeyId}/experience`);
  await page.goto(BASE + "/v8/authoritative", {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForTimeout(1500);
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const replanAction =
    (await page.locator('[data-testid="recovery-replan"]').count()) > 0;
  const acknowledge =
    (await page.locator('[data-testid="recovery-acknowledge"]').count()) > 0;
  results.flows.push({
    viewport: vp.name,
    flow: "MIDTRIP_HARD_RECOVERY",
    start_before: picked.start.status,
    confirm_status: confirmed.status,
    confirm_recovery: confirmed.body && confirmed.body.recovery
      ? confirmed.body.recovery.state
      : null,
    experience_recovery: experience.body && experience.body.recovery
      ? experience.body.recovery.state
      : null,
    experience_needs_review: experience.body && experience.body.experience_flags
      ? experience.body.experience_flags.needs_review
      : null,
    ui_panel_visible: visible,
    ui_replan_action: replanAction,
    ui_acknowledge_action: acknowledge,
    page_errors: pageErrors.slice(0, 3),
  });
  return picked;
}

async function staleFlow(browser, vp, results, page, pageErrors) {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  // The stale condition is prepared out of band (see expire_evidence.py): the
  // selected plan's frozen evidence has already been expired in the database.
  const staleStart = await api(`/journeys/${journeyId}/start`, {
    method: "POST",
  });
  const experience = await api(`/journeys/${journeyId}/experience`);
  await page.goto(BASE + "/v8/authoritative", {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForTimeout(1500);
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const title =
    visible
      ? await page.locator('[data-testid="recovery-required-title"]').innerText()
      : null;
  results.flows.push({
    viewport: vp.name,
    flow: "STALE_EVIDENCE_WARNING",
    start_status: staleStart.status,
    start_message: String(
      (staleStart.body && staleStart.body.error && staleStart.body.error.message) || "",
    ).slice(0, 140),
    journey_status_after: (
      await api(`/journeys/${journeyId}`)
    ).body.status,
    experience_flags_staleness:
      experience.body && experience.body.experience_flags
        ? experience.body.experience_flags.staleness
        : null,
    ui_panel_visible: visible,
    ui_title: title,
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
      geolocation:
        gps === "allowed" ? { latitude: 39.1, longitude: 117.18 } : undefined,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto(BASE + "/v8/live", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForTimeout(1500);
    const state = await page.evaluate(() => ({
      textLength: document.body ? document.body.innerText.length : 0,
      overflow:
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 1,
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
  const mode = process.env.PROBE_MODE || "all";
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") pageErrors.push(message.text());
    });

    if (mode === "all" || mode === "c4") {
      await c4Flow(browser, vp, results);
      await renderRoute(page, vp.name, "/v8/authoritative", results, pageErrors);
    }
    if (mode === "all" || mode === "recovery") {
      await recoveryFlow(browser, vp, results, page, pageErrors);
    }
    if (mode === "all" || mode === "stale") {
      await staleFlow(browser, vp, results, page, pageErrors);
    }
    if (mode === "all" || mode === "gps") {
      await gpsFlow(browser, vp, results);
    }
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

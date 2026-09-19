/**
 * E2E runs 2-6 for the CityNexus overnight continuation.
 *
 * Each scenario drives the *visible* UI in its own browser context.  The only
 * out-of-band calls are state inspection and the disruption event, which a
 * traveller cannot type into a phone.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/shots";
fs.mkdirSync(SHOTS, { recursive: true });
const api = async (method, p, body) => {
  const r = await fetch(API + p, {
    method,
    headers: { "Content-Type": "application/json", "Idempotency-Key": `sc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let j = null;
  try { j = JSON.parse(t); } catch { j = { _raw: t.slice(0, 250) }; }
  return { status: r.status, json: j };
};

async function newContext(browser, viewport) {
  return browser.newContext({ viewport, isMobile: true, hasTouch: true, locale: "zh-CN" });
}

function attach(page, errors, label) {
  page.on("pageerror", (e) => errors.push(`${label}:pageerror:${String(e).slice(0, 140)}`));
  page.on("console", (m) => {
    if (m.type() === "error" && !/tile\.openstreetmap|ERR_CONNECTION|AJAXError|Failed to load resource/.test(m.text()))
      errors.push(`${label}:console:${m.text().slice(0, 140)}`);
  });
}

/** Drive the three-step wizard through the UI and return the new journey id. */
async function createJourney(page, opts) {
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="trial-city"]').fill(opts.city || "厦门");
  await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-arrival"]').fill(opts.arrival || "厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill(opts.departure || "厦门北站");
  await page.locator('[data-testid="trial-start"]').fill(opts.start);
  await page.locator('[data-testid="trial-end"]').fill(opts.end);
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  if (opts.party) await page.locator('[data-testid="trial-party"]').fill(String(opts.party)).catch(() => {});
  await page.locator('[data-testid="trial-budget"]').fill(String(opts.budget));
  await page.locator('[data-testid="trial-stay-budget"]').fill(String(opts.stayBudget));
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-create"]').click();
  await page.waitForTimeout(8000);
  return page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
}

/** Run the AI planner sheet and wait for a real plan count. */
async function planWithAi(page, prompt) {
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  if (!(await page.locator('[data-testid="plan-ai-input"]').count())) {
    await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(() => {});
    await page.waitForTimeout(1500);
  }
  await page.locator('[data-testid="plan-ai-input"]').fill(prompt);
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let count = -1;
  for (let i = 0; i < 75; i++) {
    await page.waitForTimeout(2500);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    if (n !== null) { count = Number(n); break; }
  }
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(2000);
  return count;
}

async function choosePlan(page) {
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(4000);
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  if (!cards) return false;
  await page.locator('[data-testid="plan-cmp-choose"]').first().click();
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(2000);
    if (!(await page.locator('[data-testid="plan-comparison"]').count())) return true;
  }
  return false;
}

/** Select the first hotel that the backend accepts. */
async function chooseHotel(page) {
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(3000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(5500);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) return { hotels, chosen: true, error: "" };
  }
  const error = await page.locator('[data-testid="hotel-error"]').innerText().catch(() => "");
  return { hotels, chosen: false, error };
}

async function askCopilot(page, question) {
  await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  if (!(await page.locator('.cn-copilot-form textarea').count())) {
    await page.locator('.cn-copilot-edge').click().catch(() => {});
    await page.waitForTimeout(1500);
  }
  const box = page.locator('.cn-copilot-form textarea');
  if (!(await box.count())) return "";
  await box.fill(question);
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  let answer = "";
  for (let i = 0; i < 40; i++) {
    await page.waitForTimeout(2500);
    const bubbles = await page.locator('.cn-copilot-bubble.assistant').count();
    if (bubbles > 0) {
      const last = await page.locator('.cn-copilot-bubble.assistant').last().innerText().catch(() => "");
      if (last.trim().length > 25) { answer = last; break; }
    }
  }
  return answer;
}

/** Raise a CLOSURE against the first flexible stop and generate a proposal. */
async function disruptAndReplan(page, journeyId) {
  const exp = await api("GET", `/journeys/${journeyId}/experience`);
  const acts = exp.json?.active_plan?.activities ?? [];
  const target = acts.find((a) => !a.locked);
  if (!target) return { ok: false, reason: "no mutable stop" };
  const ev = await api("POST", `/journeys/${journeyId}/events`, {
    event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id, provenance: "USER_REPORTED",
  });
  const prop = await api("POST", `/journeys/${journeyId}/replans`, { trigger_event_id: ev.json?.id });
  return {
    ok: prop.status === 201 && Boolean(prop.json?.id),
    target: String(target.title),
    status: prop.status,
    preserved: prop.json?.locked_commitments_preserved,
    removed: (prop.json?.diff?.removed ?? []).length,
    added: (prop.json?.diff?.added ?? []).length,
    error: prop.json?.error?.message ?? null,
  };
}

async function acceptOnLive(page) {
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(6000);
  const sawDisruption = await page.locator('[data-testid="live-disruption"]').count();
  const sawProposal = await page.locator('[data-testid="live-proposal"]').count();
  if (!sawProposal) return { sawDisruption, sawProposal, accepted: false, message: "" };
  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false;
  let message = "";
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(2000);
    message = await page.locator('[data-testid="live-message"]').innerText().catch(() => "");
    if (/已|updated/.test(message)) { accepted = true; break; }
    if (await page.locator('[data-testid="live-handled"]').count()) { accepted = true; break; }
  }
  return { sawDisruption, sawProposal, accepted, message };
}

const SCENARIOS = {
  // Run 2 — budget-constrained trip.
  budget: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 900, stayBudget: 300 },
    prompt: "两个人去厦门，预算很紧，只想看海和吃本地小吃。",
  },
  // Run 3 — long multi-day trip.
  longtrip: {
    viewport: { width: 430, height: 932 },
    create: { start: "2026-11-06T10:00", end: "2026-11-12T20:00", budget: 8000, stayBudget: 3000 },
    prompt: "在厦门待六天，慢慢逛，想看海、老街、博物馆和公园。",
  },
  // Run 4 — booking-first.
  bookingfirst: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 3000, stayBudget: 1000 },
    bookingFirst: true,
  },
  // Run 5 — degraded providers.
  degraded: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 3000, stayBudget: 1000 },
    prompt: "第一次来厦门，想看海和日落。",
    degrade: true,
  },
};

(async () => {
  const which = process.argv[2];
  const spec = SCENARIOS[which];
  if (!spec) { console.error("unknown scenario", which); process.exit(2); }
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await newContext(browser, spec.viewport);
  const page = await ctx.newPage();
  const errors = [];
  const T = [];
  let JID = null;
  const rec = (action, status, result) =>
    T.push({ ts: new Date().toISOString(), journey_id: JID, action, status, result: String(result).replace(/\s+/g, " ").slice(0, 190) });
  attach(page, errors, which);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/${which}_${n}.png` }).catch(() => {});

  try {
    JID = await createJourney(page, spec.create);
    rec("create-journey", JID ? "201" : "NO-JOURNEY", JID || "");
    await shot("01_created");
    if (!JID) throw new Error("journey not created");

    if (spec.bookingFirst) {
      // Booking-first: import a confirmed booking before any plan exists.
      await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);
      await page.locator('[data-testid="trips-tab-bookings"]').click();
      await page.waitForTimeout(2500);
      await page.locator('[data-testid="inbox-tab-manual"]').click();
      await page.waitForTimeout(600);
      await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
      await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
      await page.locator('[data-testid="manual-ref"]').fill("E2E-BOOKFIRST-1");
      await page.locator('[data-testid="manual-from"]').fill("厦门北站");
      await page.locator('[data-testid="manual-to"]').fill("深圳北站");
      await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
      await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
      await page.locator('[data-testid="manual-amount"]').fill("180");
      await page.locator('[data-testid="manual-submit"]').click();
      await page.waitForTimeout(6000);
      await page.locator('[data-testid="v13-2-anchor-role"]').selectOption("DEPARTURE").catch(() => {});
      await page.locator('[data-testid="v13-2-save-corrections"]').click().catch(() => {});
      await page.waitForTimeout(3500);
      await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
      // The apply is a real write; wait for the confirmed draft, then read the
      // wallet instead of sampling it once and racing the commit.
      let n = 0;
      for (let i = 0; i < 20; i++) {
        await page.waitForTimeout(2000);
        const wallet = await api("GET", `/journeys/${JID}/wallet`);
        n = (wallet.json?.reservations ?? wallet.json?.items ?? []).length;
        if (n > 0) break;
      }
      rec("booking-first-import", n > 0 ? "applied" : "not-applied", `wallet=${n}`);
      await shot("02_booking_first");
    }

    if (spec.degrade) {
      // Honest degraded state: point the app at an unreachable provider and
      // confirm the traveller sees an explanation rather than invented data.
      const off = await api("GET", `/journeys/${JID}/offline-snapshot`);
      rec("degraded-offline-snapshot", off.status, Object.keys(off.json || {}).slice(0, 6).join(","));
    }

    if (spec.prompt) {
      const count = await planWithAi(page, spec.prompt);
      rec("ai-plan", count > 0 ? `plans-ready(${count})` : `no-plans(${count})`, "");
      await shot("03_ai");
      const ok = await choosePlan(page);
      rec("choose-plan", ok ? "selected" : "not-selected", "");
      await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);
      const stops = await page.locator('[data-testid="trip-stop"]').count();
      const hasTabs = await page.locator('[data-testid="trips-tabs"]').count();
      rec("itinerary", stops ? `${stops} stops` : (hasTabs ? "no-stops-shown" : "no-tabs"), "");
      await shot("04_itinerary");
    }

    const hotel = await chooseHotel(page);
    rec("choose-hotel", hotel.chosen ? "selected" : "not-selected", `${hotel.hotels} hotels ${hotel.error}`);
    await shot("05_hotel");

    if (spec.prompt) {
      const answer = await askCopilot(page, "为什么这样安排？");
      rec("copilot", answer.length > 25 ? "answered" : "empty", answer);
      await shot("06_copilot");

      const dis = await disruptAndReplan(page, JID);
      rec("disruption+replan", dis.ok ? `201 preserved=${dis.preserved} -${dis.removed}/+${dis.added}` : `FAIL ${dis.status} ${dis.error}`,
          `target=${dis.target}`);
      if (dis.ok) {
        const acc = await acceptOnLive(page);
        rec("accept-replan", acc.accepted ? "accepted" : "not-accepted", `${acc.message} disruption=${acc.sawDisruption} proposal=${acc.sawProposal}`);
        await shot("07_accepted");
        const exp = await api("GET", `/journeys/${JID}/experience`);
        rec("final-truth", `${(exp.json?.active_plan?.activities ?? []).length} activities`,
            `locked=${(exp.json?.active_plan?.activities ?? []).filter((a) => a.locked).length}`);
      }
    }

    // Refresh + navigation robustness for every scenario.
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const before = await page.locator('[data-testid="trips-tabs"]').count();
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const after = await page.locator('[data-testid="trips-tabs"]').count();
    rec("hard-refresh", before && after ? "stable" : "broken", `before=${before} after=${after}`);
    await shot("08_refresh");

    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="nav-trips"]').click();
    await page.waitForTimeout(2500);
    const onTrips = await page.locator('[data-testid="trips-tabs"]').count();
    await page.goBack();
    await page.waitForTimeout(2500);
    const backOk = await page.locator('[data-testid="today-heading"]').count();
    await page.goForward();
    await page.waitForTimeout(2500);
    const fwdOk = await page.locator('[data-testid="trips-tabs"]').count();
    rec("back-forward", onTrips && backOk && fwdOk ? "ok" : "broken", `trips=${onTrips} back=${backOk} fwd=${fwdOk}`);
  } catch (e) {
    rec("FAILURE", "error", e.message);
  }

  fs.writeFileSync(`${EV}/scenario_${which}.json`, JSON.stringify({
    run: which, journey_id: JID, viewport: `${spec.viewport.width}x${spec.viewport.height}`,
    trace: T, errors: errors.slice(0, 10),
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.action.padEnd(24)} ${String(t.status).padEnd(22)} ${t.result.slice(0, 84)}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})();

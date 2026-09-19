/**
 * V15 Night Lab — frontend user-journey trial.
 *
 * Drives the real UI in a real Chromium against the *isolated* stack:
 *   vite 4173  ->  uvicorn 8010  ->  this workspace's own citynexus.db
 * It never touches the Codex worktree, nor the servers Codex is running on
 * 5173/8000.
 *
 * What it records, because these are the things a real user would notice:
 *   - uncaught page errors, console errors, failed / 4xx / 5xx requests
 *   - the visible text of every top-level view, plus a screenshot
 *   - what actually happens to authoritative state after realistic messages
 *     typed into the AI desk, read back from the backend (not from the DOM)
 *
 * Usage:
 *   node _v15_trial/ui_trial.mjs            # full run
 *   node _v15_trial/ui_trial.mjs --explore  # landing page only
 */
import { chromium } from "playwright-core";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = "http://127.0.0.1:4173";
const API = "http://127.0.0.1:8010";
const OUT = "D:/moodle/CityNexus-Tools/WorkBuddy-V15-NightLab-20260914/evidence/ui_trial";
const EXPLORE = process.argv.includes("--explore");

mkdirSync(OUT, { recursive: true });

const report = {
  base: BASE,
  api: API,
  consoleErrors: [],
  pageErrors: [],
  badRequests: [],
  views: [],
  aiDesk: [],
  notes: [],
};

const log = (...a) => console.log(...a);

async function api(path) {
  try {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) return { error: `HTTP ${res.status}` };
    return await res.json();
  } catch (e) {
    return { error: String(e) };
  }
}

/** Authoritative state snapshot — read from the backend, never from the DOM. */
async function snapshot(journeyId) {
  if (!journeyId) return { error: "no journey id" };
  const [journey, events, guardian] = await Promise.all([
    api(`/api/v1/journeys/${journeyId}`),
    api(`/api/v1/journeys/${journeyId}/events`),
    api(`/api/v1/journeys/${journeyId}/guardian/status`),
  ]);
  const runs = guardian?.runs ?? [];
  return {
    plan_version_id: journey?.plan_version_id ?? journey?.current_plan_version_id ?? null,
    status: journey?.status ?? null,
    currency: journey?.currency ?? null,
    timezone: journey?.timezone ?? null,
    city: journey?.city ?? journey?.destination_city ?? null,
    event_count: Array.isArray(events) ? events.length : null,
    event_types: Array.isArray(events) ? events.map((e) => e.event_type) : null,
    mission_count: runs.length,
    mission_titles: runs.map((r) => r.mission?.title ?? r.title ?? r.trigger_kind ?? null),
    mission_kinds: runs.map((r) => r.trigger_kind ?? null),
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
  });
  const page = await context.newPage();

  page.on("console", (m) => {
    if (m.type() === "error") {
      report.consoleErrors.push({ text: m.text().slice(0, 400), url: page.url() });
    }
  });
  page.on("pageerror", (e) => {
    report.pageErrors.push({ message: String(e).slice(0, 600), url: page.url() });
  });
  page.on("response", (r) => {
    if (r.status() >= 400) {
      report.badRequests.push({ status: r.status(), method: r.request().method(), url: r.url() });
    }
  });

  // ---------------------------------------------------------------- landing
  log(`opening ${BASE}/v8/live ...`);
  await page.goto(`${BASE}/v8/live`, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(3500);

  const landingText = (await page.locator("body").innerText().catch(() => "")).slice(0, 4000);
  await page.screenshot({ path: join(OUT, "01-landing.png") });
  report.views.push({ view: "landing", url: page.url(), text: landingText });

  if (EXPLORE) {
    await browser.close();
    writeFileSync(join(OUT, "00-explore.json"), JSON.stringify(report, null, 2), "utf8");
    log("explore mode: stopping");
    return;
  }

  // ------------------------------------------------------- bootstrap journey
  log("clicking 'Use the sealed Tianjin demo' ...");
  let bootstrapped = false;
  try {
    await page.click('[data-testid="trial-tianjin-demo"]', { timeout: 15000 });
    await page.waitForTimeout(9000);
    bootstrapped = true;
  } catch (e) {
    report.notes.push(`bootstrap click failed: ${String(e).slice(0, 200)}`);
  }
  const afterBootstrap = (await page.locator("body").innerText().catch(() => "")).slice(0, 4000);
  await page.screenshot({ path: join(OUT, "02-after-bootstrap.png") });
  report.views.push({ view: "after-bootstrap", url: page.url(), text: afterBootstrap });

  const journeyId = await page
    .evaluate(() => window.localStorage.getItem("citynexus.v8.journey_id"))
    .catch(() => null);
  log(`journey id from localStorage: ${journeyId}`);
  report.journeyId = journeyId;
  report.baseline = await snapshot(journeyId);
  log(`baseline: ${JSON.stringify(report.baseline)}`);

  // ------------------------------------------------------------ walk routes
  const routes = [
    "hub", "studio", "stay", "discover", "live",
    "authoritative", "bookings", "intelligence", "twin", "agent",
  ];
  for (const route of routes) {
    const url = `${BASE}/v8/${route}`;
    log(`--- /v8/${route}`);
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 40000 });
      await page.waitForTimeout(3000);
      const text = (await page.locator("body").innerText().catch(() => "")).slice(0, 6000);
      // The nav renders before the content, so also grab the content region on
      // its own — otherwise every route looks identical in the report.
      const content = await page
        .locator(".v8-page, main, [role=main]")
        .allInnerTexts()
        .then((parts) => parts.join("\n---\n").slice(0, 6000))
        .catch(() => "");
      await page.screenshot({ path: join(OUT, `view-${route}.png`) });
      report.views.push({ view: route, url, text, content });
      log(`    ${content.replace(/\s+/g, " ").slice(0, 220)}`);
    } catch (e) {
      report.views.push({ view: route, url, error: String(e).slice(0, 300) });
      log(`    ERROR ${String(e).slice(0, 160)}`);
    }
  }

  // ------------------------------------------------------------- AI desk
  await page.goto(`${BASE}/v8/agent`, { waitUntil: "domcontentloaded", timeout: 40000 });
  await page.waitForTimeout(3000);

  const submitBtn = page.locator('[data-testid="v8-agent-submit"]');
  // The button is disabled both by `busy` and by `command.trim().length < 8`.
  // To separate the two, learn the idle label first and then wait for it to come
  // back after each submit — otherwise the *previous* run's `busy` state makes
  // every later probe look length-blocked, which would be a false finding.
  const idleLabel = (await submitBtn.innerText().catch(() => "")).trim();
  log(`submit button idle label: "${idleLabel}"`);

  async function waitUntilIdle(timeoutMs = 150000) {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
      const label = (await submitBtn.innerText().catch(() => "")).trim();
      if (label === idleLabel) return true;
      await page.waitForTimeout(1500);
    }
    return false;
  }

  // (a) the product's own demo command — disruption + commitment protection + delegation
  // (b) a hypothetical — must NOT create a real Event
  // (c1) 7 chars: a REAL disruption report the UI refuses to send
  // (c2) 8 chars: the same report, padded to clear the gate — must not fabricate
  // (d) a preference — must NOT create a real Event
  const probes = [
    {
      label: "a_demo_command",
      text: "下午海河沿线有交通管制，我不想淋雨，游船和晚餐别动，最多多花50元。你自己重新安排。",
      note: "the product's own default command: disruption + protected commitments + delegation",
    },
    {
      label: "b_hypothetical_rain",
      text: "如果下雨会怎样？",
      note: "WHAT_IF (8 chars) — must not create a real Event",
    },
    {
      label: "c1_short_real_rain_7",
      text: "现在正在下雨。",
      note: "REAL disruption, 7 chars — exercises the min_length=8 gate",
    },
    {
      label: "c2_real_rain_padded_8",
      text: "现在正在下雨了。",
      note: "the same real disruption padded to 8 chars — does it still fabricate a WEATHER event?",
    },
    {
      label: "d_preference",
      text: "我想少走路。",
      note: "preference (6 chars) — must not create a real Event",
    },
  ];

  for (const probe of probes) {
    const entry = { ...probe };
    await waitUntilIdle();
    entry.before = await snapshot(journeyId);
    try {
      await page.fill("#v8-agent-input", probe.text);
      // Give React a full tick to re-render the controlled textarea and the
      // derived `disabled` prop before reading it.
      await page.waitForTimeout(1200);
      const domValue = await page.inputValue("#v8-agent-input").catch(() => null);
      entry.char_length = probe.text.length;
      entry.dom_length = domValue ? domValue.length : null;
      entry.dom_value_matches = domValue === probe.text;
      entry.submit_disabled = await submitBtn.isDisabled();

      if (entry.submit_disabled) {
        entry.outcome = "BLOCKED_BY_UI — submit button disabled";
        log(`[${probe.label}] ${entry.outcome} (len=${probe.text.length})`);
      } else {
        await submitBtn.click();
        await page.waitForTimeout(2500);
        const stillWorking = (await submitBtn.innerText().catch(() => "")).trim() !== idleLabel;
        entry.busy_after_click = stillWorking;
        const idle = await waitUntilIdle();
        entry.completed_within_timeout = idle;
        entry.outcome = idle ? "submitted_and_completed" : "submitted_but_still_busy";
        entry.visible_text = (await page.locator("body").innerText().catch(() => "")).slice(0, 2500);
        log(`[${probe.label}] ${entry.outcome} (len=${probe.text.length})`);
      }
    } catch (e) {
      entry.outcome = `ERROR ${String(e).slice(0, 250)}`;
      log(`[${probe.label}] ${entry.outcome}`);
    }
    entry.after = await snapshot(journeyId);
    entry.delta = {
      events: (entry.after.event_count ?? 0) - (entry.before.event_count ?? 0),
      missions: (entry.after.mission_count ?? 0) - (entry.before.mission_count ?? 0),
      plan_version_changed: entry.after.plan_version_id !== entry.before.plan_version_id,
      new_event_types: entry.after.event_types ?? null,
    };
    report.aiDesk.push(entry);
    await page.screenshot({ path: join(OUT, `ai-${probe.label}.png`) });
  }

  // ------------------------------------------------------- mobile viewport
  log("--- mobile viewport 390x844");
  const mobile = await context.newPage();
  try {
    await mobile.setViewportSize({ width: 390, height: 844 });
    await mobile.goto(`${BASE}/v8/live`, { waitUntil: "domcontentloaded", timeout: 40000 });
    await mobile.waitForTimeout(3500);
    const text = (await mobile.locator("body").innerText().catch(() => "")).slice(0, 2500);
    await mobile.screenshot({ path: join(OUT, "mobile-live.png") });
    report.views.push({ view: "mobile-live", text });
    log(`    ${text.replace(/\s+/g, " ").slice(0, 160)}`);
  } catch (e) {
    report.views.push({ view: "mobile-live", error: String(e).slice(0, 250) });
  }
  await mobile.close();

  await browser.close();

  report.summary = {
    console_error_count: report.consoleErrors.length,
    page_error_count: report.pageErrors.length,
    bad_request_count: report.badRequests.length,
    bootstrapped,
  };
  writeFileSync(join(OUT, "trial_report.json"), JSON.stringify(report, null, 2), "utf8");
  log("");
  log("================ SUMMARY ================");
  log(JSON.stringify(report.summary, null, 2));
  log(`report: ${join(OUT, "trial_report.json")}`);
}

main().catch((err) => {
  console.error("TRIAL FAILED:", err);
  writeFileSync(join(OUT, "trial_report.json"), JSON.stringify(report, null, 2), "utf8");
  process.exit(1);
});

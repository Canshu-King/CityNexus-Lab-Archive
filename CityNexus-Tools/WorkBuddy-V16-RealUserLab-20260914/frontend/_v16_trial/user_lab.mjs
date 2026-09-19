// V16 Real-User Lab — drive the *real* product UI as a traveller would.
//
// For each persona in tools/v16_realuser/matrix.json this script:
//   1. opens the app in a browser context pinned to the persona's timezone
//   2. fills the journey-creation form exactly as a human would
//   3. walks every route a curious user would visit
//   4. types the persona's own words into the AI desk and submits them
//   5. records every HTTP status, console error, page error and screenshot
//
// It never calls the API directly for *mutations* — only reads authoritative
// state back out of the backend so the report can prove what really changed.
//
// Usage:  node _v16_trial/user_lab.mjs --persona=P01_couple_late_night
//         node _v16_trial/user_lab.mjs --all

import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const BASE = process.env.V16_BASE || "http://127.0.0.1:4173";
const API = process.env.V16_API || "http://127.0.0.1:8010/api/v1";
const OUT = path.join(ROOT, "evidence", "v16_lab");
const SHOTS = path.join(OUT, "screenshots");

const MATRIX = JSON.parse(
  fs.readFileSync(path.join(ROOT, "tools", "v16_realuser", "matrix.json"), "utf-8"),
);

const PARTY_SIZE = {
  P01_couple_late_night: 2,
  P02_county_honeymoon: 2,
  P03_elderly_parents: 3,
  P04_infant_family: 3,
  P05_student_shoestring: 1,
  P06_family_two_kids: 4,
  P07_solo_backpacker_en: 1,
  P08_business_tokyo: 1,
  P09_group_of_six: 6,
  P10_budget_hunter: 2,
  P11_photographer: 1,
  P12_wheelchair_user: 2,
};

const ARRIVAL = {
  P01_couple_late_night: "11:30",
  P02_county_honeymoon: "10:20",
  P03_elderly_parents: "12:40",
  P04_infant_family: "13:10",
  P05_student_shoestring: "06:40",
  P06_family_two_kids: "09:40",
  P07_solo_backpacker_en: "08:30",
  P08_business_tokyo: "07:10",
  P09_group_of_six: "10:30",
  P10_budget_hunter: "09:20",
  P11_photographer: "04:40",
  P12_wheelchair_user: "09:00",
};

const DEPARTURE = {
  P01_couple_late_night: "19:00",
  P02_county_honeymoon: "16:00",
  P03_elderly_parents: "15:30",
  P04_infant_family: "14:00",
  P05_student_shoestring: "20:30",
  P06_family_two_kids: "17:00",
  P07_solo_backpacker_en: "18:00",
  P08_business_tokyo: "20:00",
  P09_group_of_six: "19:30",
  P10_budget_hunter: "18:30",
  P11_photographer: "17:30",
  P12_wheelchair_user: "16:30",
};

const ARRIVAL_PLACE = {
  CN: (p) => `${p.city}站`,
  GB: () => "London Paddington",
  JP: (p) => `${p.city}駅`,
  SG: () => "Changi Airport T3",
};
const DEPARTURE_PLACE = {
  CN: (p) => `${p.city}机场`,
  GB: () => "London Heathrow T5",
  JP: (p) => `${p.city}空港`,
  SG: () => "Changi Airport T1",
};

const ROUTES = [
  "hub",
  "studio",
  "stay",
  "discover",
  "live",
  "map",
  "bookings",
  "intelligence",
  "twin",
  "authoritative",
  "agent",
  "me",
];

const DAY0 = process.env.V16_DAY0 || "2026-10-09";

function pad(n) {
  return String(n).padStart(2, "0");
}

function addDays(isoDate, days) {
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + days);
  return `${dt.getUTCFullYear()}-${pad(dt.getUTCMonth() + 1)}-${pad(dt.getUTCDate())}`;
}

function minorToMajor(minor, currency) {
  const zeroDecimal = new Set(["JPY", "KRW", "VND", "IDR"]);
  return zeroDecimal.has(currency) ? minor : minor / 100;
}

async function api(pathname) {
  try {
    const res = await fetch(`${API}${pathname}`);
    const text = await res.text();
    let body = null;
    try {
      body = JSON.parse(text);
    } catch {
      body = text.slice(0, 400);
    }
    return { status: res.status, body };
  } catch (error) {
    return { status: 0, body: String(error) };
  }
}

async function runPersona(browser, persona, injections) {
  const pid = persona.pid;
  const context = await browser.newContext({
    timezoneId: persona.timezone,
    locale: persona.country === "CN" ? "zh-CN" : "en-GB",
    viewport: { width: 1440, height: 960 },
  });
  const page = await context.newPage();

  const record = {
    persona: persona.pid,
    label_zh: persona.label_zh,
    city: persona.city,
    city_code: persona.city_code,
    timezone: persona.timezone,
    currency: persona.currency,
    wake_time: persona.wake_time,
    bed_time: persona.bed_time,
    quirks: persona.quirks,
    console_errors: [],
    page_errors: [],
    failed_requests: [],
    http_errors: [],
    steps: [],
    journey_id: null,
    plan: null,
    injections: [],
    ai_desk: [],
  };

  page.on("console", (msg) => {
    if (msg.type() === "error") record.console_errors.push(msg.text().slice(0, 400));
  });
  page.on("pageerror", (err) => record.page_errors.push(String(err).slice(0, 400)));
  page.on("requestfailed", (req) => {
    record.failed_requests.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText}`);
  });
  page.on("response", (res) => {
    const status = res.status();
    if (status >= 400) {
      record.http_errors.push(`${status} ${res.request().method()} ${res.url()}`);
    }
  });

  const shot = async (name) => {
    try {
      await page.screenshot({
        path: path.join(SHOTS, `${pid}__${name}.png`),
        fullPage: false,
      });
    } catch {
      /* screenshot is best-effort */
    }
  };

  const mark = (text) => process.stdout.write(`    [${pid}] ${text}\n`);

  // ---------------------------------------------------------------- step 1
  // Create the journey through the real setup form.
  const day0 = DAY0;
  const dayN = addDays(day0, persona.days);
  const arrivalPlace = (ARRIVAL_PLACE[persona.country] || ARRIVAL_PLACE.CN)(persona);
  const departurePlace = (DEPARTURE_PLACE[persona.country] || DEPARTURE_PLACE.CN)(persona);
  const draft = {
    city: persona.city,
    country: persona.country,
    timezone: persona.timezone,
    start: `${day0}T${ARRIVAL[pid]}`,
    end: `${dayN}T${DEPARTURE[pid]}`,
    arrival: arrivalPlace,
    departure: departurePlace,
    budgetMajor: minorToMajor(persona.budget_minor, persona.currency),
    stayMajor: minorToMajor(persona.stay_budget_minor, persona.currency),
    currency: persona.currency,
    party: PARTY_SIZE[pid] ?? 2,
  };
  record.draft = draft;

  mark("opening setup");
  await page.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForSelector('[data-testid="trial-setup"]', { timeout: 30000 });

  // Only 8 of the 11 inputs on this form carry a data-testid. The three money
  // fields and the party size do not, so they have to be addressed
  // structurally — itself a small finding about the form's test hooks.
  const row3 = '[data-testid="trial-setup"] .v8-trial-row.three';
  await page.fill('[data-testid="trial-city"]', draft.city);
  await page.fill('[data-testid="trial-country"]', draft.country);
  await page.fill('[data-testid="trial-timezone"]', draft.timezone);
  await page.fill('[data-testid="trial-start"]', draft.start);
  await page.fill('[data-testid="trial-end"]', draft.end);
  await page.fill('[data-testid="trial-arrival"]', draft.arrival);
  await page.fill('[data-testid="trial-departure"]', draft.departure);
  await page.fill(`${row3} input[type="number"] >> nth=0`, String(draft.budgetMajor));
  await page.fill(`${row3} input:not([type="number"])`, draft.currency);
  await page.fill(`${row3} input[type="number"] >> nth=1`, String(draft.party));
  await page.fill(
    '[data-testid="trial-setup"] .v8-trial-form > label:last-of-type input',
    String(draft.stayMajor),
  );
  await shot("01_setup_filled");

  mark("submitting journey form");
  const createResp = page
    .waitForResponse((r) => r.url().includes("/stay-options/generate"), { timeout: 90000 })
    .catch(() => null);
  await page.click('[data-testid="trial-create"]');
  await createResp;
  await page.waitForTimeout(2500);

  mark("reading journey id");
  record.journey_id = await page.evaluate(() =>
    window.localStorage.getItem("citynexus.v8.journey_id"),
  );
  record.setup_error = await page
    .locator(".v8-trial-setup ~ *")
    .first()
    .textContent()
    .catch(() => null);
  await shot("02_after_create");
  record.steps.push({ step: "create", url: page.url(), journey_id: record.journey_id });

  if (record.journey_id) {
    const exp = await api(`/journeys/${record.journey_id}/experience`);
    const options = exp.body?.options ?? [];
    record.plan = {
      experience_status: exp.status,
      option_count: options.length,
      selected_option_id: exp.body?.selected_option_id ?? null,
      stay_property: options[0]?.stay?.property_name ?? null,
      days: (options[0]?.days ?? []).map((d) => ({
        day: d.day,
        label: d.label,
        anchor: d.anchor,
        mode: d.mode,
        activities: (d.activities ?? []).map((a) => ({
          id: a.id,
          title: a.title,
          start_at: a.start_at,
          end_at: a.end_at,
          location: a.location,
          locked: a.locked,
          type: a.type ?? a.kind ?? null,
        })),
      })),
    };
    record.stay_options = await api(`/journeys/${record.journey_id}/stay-options`);
    record.stay_generate = await api(`/journeys/${record.journey_id}/stay-options/generate`);
  }

  // ---------------------------------------------------------------- step 2
  // Walk every route a curious traveller would open.
  mark("walking routes");
  for (const route of ROUTES) {
    await page.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(1200);
    const bodyText = (await page.locator("body").innerText().catch(() => "")).slice(0, 900);
    record.steps.push({ step: `route:${route}`, url: page.url(), text: bodyText });
    await shot(`route_${route}`);
  }

  // ---------------------------------------------------------------- step 3
  // The AI desk: the persona says what it really says.
  await page.goto(`${BASE}/v8/agent`, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForSelector('[data-testid="v8-agent-input"]', { timeout: 30000 });

  const submitMessage = async (label, message) => {
    const input = page.locator('[data-testid="v8-agent-input"]');
    const button = page.locator('[data-testid="v8-agent-submit"]');
    await input.fill(message);
    const disabled = await button.isDisabled();
    const entry = {
      label,
      message,
      chars: message.trim().length,
      submit_disabled: disabled,
      blocked_reason: disabled ? "SUBMIT_BUTTON_DISABLED" : null,
    };
    if (disabled) {
      record.ai_desk.push(entry);
      await shot(`agent_blocked_${label}`);
      return entry;
    }
    const commands = page
      .waitForResponse((r) => r.url().includes("/agent/commands"), { timeout: 90000 })
      .catch(() => null);
    await button.click();
    const res = await commands;
    entry.http_status = res ? res.status() : null;
    if (res) {
      try {
        entry.response = JSON.parse((await res.text()).slice(0, 4000));
      } catch {
        entry.response = null;
      }
    }
    await page.waitForTimeout(2500);
    const banner = await page
      .locator(".v8-toast, .v8-banner, [role=status]")
      .first()
      .textContent()
      .catch(() => null);
    entry.ui_banner = banner;
    record.ai_desk.push(entry);
    await shot(`agent_${label}`);
    return entry;
  };

  mark("ai desk: self description");
  await submitMessage("self_description", persona.self_description_zh);

  const before = record.journey_id ? await api(`/journeys/${record.journey_id}/events`) : null;
  record.events_before = (before?.body ?? []).length;

  for (const iid of injections) {
    const injection = MATRIX.injections.find((i) => i.iid === iid);
    if (!injection) continue;
    mark(`ai desk: ${iid}`);
    const entry = await submitMessage(iid, injection.message_zh);
    entry.injection = injection;
    if (record.journey_id) {
      const ev = await api(`/journeys/${record.journey_id}/events`);
      entry.events_after = (ev.body ?? []).length;
      const guard = await api(`/journeys/${record.journey_id}/guardian/status`);
      entry.guardian = guard.body;
      const twin = await api(`/journeys/${record.journey_id}/twin`);
      entry.twin = twin.body;
    }
  }

  // ---------------------------------------------------------------- step 4
  // Read the authoritative state back out of the backend.
  if (record.journey_id) {
    record.final = {
      journey: await api(`/journeys/${record.journey_id}`),
      events: await api(`/journeys/${record.journey_id}/events`),
      guardian: await api(`/journeys/${record.journey_id}/guardian/status`),
      twin: await api(`/journeys/${record.journey_id}/twin`),
      memory: await api(`/journeys/${record.journey_id}/memory`),
      constraints: await api(`/journeys/${record.journey_id}/constraints`),
      experience: await api(`/journeys/${record.journey_id}/experience`),
      agent_feed: await api(`/journeys/${record.journey_id}/agent-feed`),
    };
  }

  mark("done");
  await context.close();
  return record;
}

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  const args = process.argv.slice(2);
  const all = args.includes("--all");
  const only = args
    .filter((a) => a.startsWith("--persona="))
    .map((a) => a.slice("--persona=".length));
  const selected = all
    ? MATRIX.personas
    : MATRIX.personas.filter((p) => only.includes(p.pid));

  if (!selected.length) {
    console.error("no persona selected; use --all or --persona=<pid>");
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  const summary = [];
  for (const persona of selected) {
    const row = MATRIX.matrix.find((m) => m[0] === persona.pid);
    const injections = row ? row[1] : [];
    process.stdout.write(`\n=== ${persona.pid} (${persona.city}) ===\n`);
    let record;
    try {
      record = await runPersona(browser, persona, injections);
    } catch (error) {
      record = { persona: persona.pid, fatal: String(error).slice(0, 800) };
    }
    fs.writeFileSync(
      path.join(OUT, `${persona.pid}.json`),
      JSON.stringify(record, null, 1),
      "utf-8",
    );
    const options = record.plan?.option_count ?? "n/a";
    process.stdout.write(
      `    options=${options} http_errors=${(record.http_errors || []).length} ` +
        `console_errors=${(record.console_errors || []).length} ` +
        `page_errors=${(record.page_errors || []).length} ` +
        `ai_calls=${(record.ai_desk || []).length}\n`,
    );
    summary.push({
      persona: persona.pid,
      city: persona.city,
      options,
      http_errors: (record.http_errors || []).length,
      console_errors: (record.console_errors || []).length,
      page_errors: (record.page_errors || []).length,
      ai_calls: (record.ai_desk || []).length,
      blocked: (record.ai_desk || []).filter((a) => a.submit_disabled).length,
      fatal: record.fatal ?? null,
    });
  }
  await browser.close();
  fs.writeFileSync(
    path.join(OUT, "lab_summary.json"),
    JSON.stringify(summary, null, 1),
    "utf-8",
  );
  process.stdout.write(`\n${JSON.stringify(summary, null, 1)}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

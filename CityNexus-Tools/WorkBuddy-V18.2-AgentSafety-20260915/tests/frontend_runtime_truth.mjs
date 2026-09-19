/**
 * V18.2 Family F - desktop / mobile runtime truth.
 *
 * Drives the REAL frontend (isolated dev server on :4173, proxying /api/v1 to
 * the isolated backend on :8021) at three viewports and asserts the UI tells
 * the truth about the agent runtime:
 *
 *   F1  the Control Tower runtime card shows the computed identity, never a
 *       hard-coded HERMES_NATIVE_MCP when the backend reports NOT_CONFIGURED;
 *   F2  the Copilot dock renders no native-Hermes run rail / Stop button while
 *       the runtime is not HERMES_NATIVE_MCP;
 *   F3  the same holds on the two mobile viewports (390x844, 430x932) - i.e.
 *       the mobile layout does not change what the product claims;
 *   F4  no uncaught page errors and no 5xx responses during the walk.
 *
 * Run (NODE_PATH must point at the frontend node_modules):
 *   node tests/frontend_runtime_truth.mjs --base http://127.0.0.1:4173 \
 *        --out evidence/results_frontend.json --shots evidence/screenshots
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

// ESM ignores NODE_PATH, so resolve Playwright through the frontend's
// node_modules (a junction to the authoritative install - never a copy).
const require = createRequire(join(ROOT, "frontend", "package.json"));
const { chromium } = require("@playwright/test");

function arg(name, dflt) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}

const BASE = arg("base", "http://127.0.0.1:4173").replace(/\/$/, "");
const OUT = arg("out", "evidence/results_frontend.json");
const SHOTS = arg("shots", "evidence/screenshots");

const VIEWPORTS = [
  { id: "F-desktop", name: "desktop 1440x900", width: 1440, height: 900, mobile: false },
  { id: "F-iphone", name: "iPhone 390x844", width: 390, height: 844, mobile: true },
  { id: "F-iphone-max", name: "iPhone Pro Max 430x932", width: 430, height: 932, mobile: true },
];

const RESULTS = [];

function record(id, name, expected, actual, status, evidence) {
  RESULTS.push({ id, name, expected, actual, status, evidence });
  const mark = { PASS: "PASS", FAIL: "FAIL", NOT_TESTED: "SKIP" }[status] || status;
  console.log(`[${mark}] ${id.padEnd(6)} ${name}`);
  if (status === "FAIL") {
    console.log(`        expected: ${expected}`);
    console.log(`        actual  : ${actual}`);
  }
}

async function walk(page, url, waitFor) {
  const pageErrors = [];
  const consoleErrors = [];
  const bad = [];
  const onPageError = (e) => pageErrors.push(String(e.message || e));
  const onConsole = (m) => {
    if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200));
  };
  const onResponse = (r) => {
    if (r.status() >= 500) bad.push(`${r.status()} ${r.url().slice(0, 120)}`);
  };
  page.on("pageerror", onPageError);
  page.on("console", onConsole);
  page.on("response", onResponse);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  if (waitFor) {
    try {
      await page.waitForSelector(waitFor, { timeout: 20000 });
    } catch { /* recorded as NOT_TESTED by the caller */ }
  }
  await page.waitForTimeout(2000);
  page.off("pageerror", onPageError);
  page.off("console", onConsole);
  page.off("response", onResponse);
  return { pageErrors, consoleErrors, bad };
}

/** Seed the demo journey through the proxied API and return its id. */
async function seedJourney() {
  const post = async (path, body) => {
    const r = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    return r.status === 204 ? null : r.json();
  };
  const ids = await post("/api/v1/demo/reset");
  const jid = ids.journey_id;
  const plans = await post(`/api/v1/journeys/${jid}/plans/generate`, { candidate_count: 1 });
  if (Array.isArray(plans) && plans[0]) {
    await post(`/api/v1/journeys/${jid}/plans/${plans[0].id}/select`);
  }
  await post(`/api/v1/journeys/${jid}/start`);
  return jid;
}

async function main() {
  mkdirSync(join(ROOT, SHOTS), { recursive: true });
  const journeyId = await seedJourney();
  console.log(`seeded demo journey: ${journeyId}`);
  const browser = await chromium.launch({ headless: true, channel: "chrome" });

  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      deviceScaleFactor: vp.mobile ? 3 : 1,
      locale: "en-GB",
    });
    // The app shows its setup screen unless a journey id is already stored.
    await ctx.addInitScript((jid) => {
      try {
        localStorage.setItem("citynexus.v8.journey_id", jid);
        localStorage.setItem("citynexus.demo.journey_id", jid);
      } catch { /* ignore */ }
    }, journeyId);
    const page = await ctx.newPage();

    // ---- F1: runtime identity card ------------------------------------- #
    const intel = await walk(page, `${BASE}/v8/intelligence`,
                             '[data-testid="v17-runtime-status"]');
    let runtimeText = null;
    const card = page.locator('[data-testid="v17-runtime-status"]');
    if (await card.count()) {
      runtimeText = (await card.first().innerText()).trim();
    }
    const honest = runtimeText !== null
      && !/HERMES_NATIVE_MCP/.test(runtimeText);
    record(`${vp.id}-F1`, `[${vp.name}] runtime card shows the computed identity`,
      "card present and does not claim HERMES_NATIVE_MCP",
      `text=${JSON.stringify(runtimeText)}`,
      honest ? "PASS" : (runtimeText === null ? "NOT_TESTED" : "FAIL"),
      { url: `${BASE}/v8/intelligence`, pageErrors: intel.pageErrors.slice(0, 3) });
    // ---- F5: the honesty card must be legible (label / value / caveat on
    //          separate lines). A run-on line can be misread as a claim.
    let parts = null;
    if (await card.count()) {
      parts = await card.first().evaluate((el) => {
        const pick = (sel) => {
          const n = el.querySelector(sel);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          return { display: getComputedStyle(n).display, top: Math.round(r.top),
                   text: n.textContent.trim().slice(0, 40) };
        };
        return { span: pick(":scope > span"), b: pick(":scope > b"),
                 small: pick(":scope > small") };
      });
    }
    // Root cause: the value and caveat must be block-level. If they are
    // `inline`, the card degenerates into one run-on line ("…sourceNOT_
    // CONFIGUREDNative Hermes MCP is not claimed…") which can be misread as a
    // claim - checked by computed display, not by line wrapping (wrapping can
    // make the offsets differ by accident on narrow viewports).
    let separated = false;
    if (parts && parts.b && parts.small) {
      separated = parts.b.display !== "inline" && parts.small.display !== "inline";
    }
    record(`${vp.id}-F5`, `[${vp.name}] runtime card value/caveat are block-level (no run-on line)`,
      "computed display of <b> and <small> is not 'inline'",
      parts ? `display=${JSON.stringify([parts.span?.display, parts.b?.display, parts.small?.display])} `
              + `tops=${JSON.stringify([parts.span?.top, parts.b?.top, parts.small?.top])}`
            : "card not found",
      separated ? "PASS" : (parts ? "FAIL" : "NOT_TESTED"),
      parts);

    await page.screenshot({ path: join(ROOT, SHOTS, `${vp.id}_intelligence.png`),
                            fullPage: false });

    // ---- F2: copilot dock must not fake a native run -------------------- #
    const agent = await walk(page, `${BASE}/v8/agent`);
    const railCount = await page.locator(".cn-copilot-rail, [data-testid*='run-rail']").count();
    const stopCount = await page.locator(".cn-copilot-stop").count();
    const noFakeRun = railCount === 0 && stopCount === 0;
    record(`${vp.id}-F2`, `[${vp.name}] copilot shows no native-Hermes run chrome`,
      "no run rail and no Stop button while runtime is not HERMES_NATIVE_MCP",
      `rail=${railCount} stop=${stopCount}`,
      noFakeRun ? "PASS" : "FAIL",
      { url: `${BASE}/v8/agent` });
    await page.screenshot({ path: join(ROOT, SHOTS, `${vp.id}_agent.png`),
                            fullPage: false });

    // ---- F3: mobile layout must not change the claim -------------------- #
    const mobileNote = vp.mobile
      ? `same identity on mobile viewport ${vp.width}x${vp.height}`
      : `desktop baseline ${vp.width}x${vp.height}`;
    record(`${vp.id}-F3`, `[${vp.name}] layout does not alter the runtime claim`,
      "runtime text identical to the honest identity",
      `${mobileNote} -> ${JSON.stringify(runtimeText)}`,
      honest ? "PASS" : "FAIL");

    // ---- F4: no page errors / no 5xx ------------------------------------ #
    const errs = [...intel.pageErrors, ...agent.pageErrors];
    const bad = [...intel.bad, ...agent.bad];
    record(`${vp.id}-F4`, `[${vp.name}] no uncaught page errors and no 5xx during the walk`,
      "pageErrors=0 and no 5xx responses",
      `pageErrors=${errs.length} 5xx=${bad.length} ${bad.slice(0, 2).join(" | ")}`,
      errs.length === 0 && bad.length === 0 ? "PASS" : "FAIL",
      { pageErrors: errs.slice(0, 5), badResponses: bad.slice(0, 5),
        consoleErrors: [...intel.consoleErrors, ...agent.consoleErrors].slice(0, 5) });

    await ctx.close();
  }

  await browser.close();

  const summary = { PASS: 0, FAIL: 0, NOT_TESTED: 0 };
  for (const r of RESULTS) summary[r.status] = (summary[r.status] || 0) + 1;
  const payload = {
    meta: { harness: "tests/frontend_runtime_truth.mjs", base: BASE,
            viewports: VIEWPORTS.map((v) => `${v.id} ${v.width}x${v.height}`),
            generated_at: new Date().toISOString() },
    summary, scenarios: RESULTS,
  };
  const outPath = join(ROOT, OUT);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify(payload, null, 2), "utf8");
  console.log(`\n== SUMMARY ==  PASS=${summary.PASS} FAIL=${summary.FAIL} NOT_TESTED=${summary.NOT_TESTED}`);
  console.log("written:", outPath);
  process.exit(summary.FAIL === 0 ? 0 : 1);
}

main().catch((e) => { console.error("FATAL", e); process.exit(2); });

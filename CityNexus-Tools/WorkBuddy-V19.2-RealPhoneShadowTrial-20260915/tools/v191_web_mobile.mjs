/**
 * V19.1 web/mobile capability-truth review.
 *
 * Drives the Snapshot-B frontend on 127.0.0.1:4213 (proxying /api/v1 to the
 * isolated backend on 8050) with system Chrome at the four mandated viewports.
 *
 * The host runs a system proxy, so the browser is forced direct.
 *
 * Measurements:
 *   - 4 viewports x reduced-motion on/off x 8 routes, screenshot + DOM analysis
 *   - a capability-state probe: declare a HARD need, then ask whether any route
 *     renders the evidence state (UNKNOWN / VERIFIED / CONFLICT)
 *   - keyboard focus order and focus visibility
 *   - 200% zoom (text-scaling) overflow
 *
 * Usage:  node tools/v191_web_mobile.mjs
 */

import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = "D:/moodle/CityNexus-Tools/WorkBuddy-V19.2-RealPhoneShadowTrial-20260915";
const require = createRequire(join(ROOT, "snapshot_a", "frontend", "package.json"));
const { chromium } = require("@playwright/test");

const BASE = "http://127.0.0.1:4213";
const API = "http://127.0.0.1:8060";
const SHOTS = join(ROOT, "evidence", "screenshots");
mkdirSync(SHOTS, { recursive: true });

const RESULTS_PATH = join(ROOT, "evidence", "web_mobile_results.json");
const FOCUS_PATH = join(ROOT, "evidence", "web_mobile_focus.json");
const CAPABILITY_PATH = join(ROOT, "evidence", "web_mobile_capability.json");

const VIEWPORTS = [
  { name: "mobile-390x844", width: 390, height: 844, mobile: true },
  { name: "mobile-430x932", width: 430, height: 932, mobile: true },
  { name: "desktop-1280x720", width: 1280, height: 720, mobile: false },
  { name: "desktop-1440x900", width: 1440, height: 900, mobile: false },
];

const ROUTES = ["hub", "live", "map", "studio", "bookings", "agent", "authoritative", "twin"];

// Vocabulary a traveller-facing surface would need in order to tell the truth
// about an accessibility need and about the evidence behind it.
const CAPABILITY_PATTERNS = [
  "capability", "step-free", "step_free", "accessib", "wheelchair", "stroller",
  "unknown evidence", "needs evidence", "needs_live_evidence", "unverified",
  "verified", "conflict", "hard", "soft", "rest window", "nap",
];

const results = [];

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    method: options.method || "GET",
    headers: { "content-type": "application/json" },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  return { status: response.status, body };
}

async function bootstrapJourney(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  await page.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(2500);

  const demo = page.getByRole("button", { name: /sealed Tianjin demo|Tianjin demo/i });
  if (!(await demo.count())) {
    throw new Error("bootstrap: the sealed-demo button was not found on /v8/hub");
  }
  await demo.first().click();
  await page.waitForTimeout(8000);

  const text = await page.evaluate(() => document.body.innerText);
  const seeded = text.includes("Journey Hub") || !text.includes("Start a real journey");
  const state = await context.storageState();
  const journeyId = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
  await context.close();
  return { state, seeded, journeyId, sample: text.slice(0, 240).replace(/\s+/g, " ") };
}

async function analyse(page, patterns) {
  return page.evaluate((pats) => {
    const text = document.body ? document.body.innerText || "" : "";
    const lower = text.toLowerCase();
    const doc = document.documentElement;

    const matches = {};
    for (const pattern of pats) matches[pattern] = lower.includes(pattern);

    const chips = Array.from(
      document.querySelectorAll(
        "[class*='chip'],[class*='badge'],[class*='pill'],[class*='status'],[class*='state']",
      ),
    );
    const namelessStatusNodes = chips
      .filter((node) => {
        const own = (node.innerText || "").trim();
        const aria = node.getAttribute("aria-label") || "";
        const title = node.getAttribute("title") || "";
        const sr = node.querySelector(".sr-only,.visually-hidden,[class*='sr-only']");
        return own.length === 0 && aria.length === 0 && title.length === 0 && !sr;
      })
      .slice(0, 12)
      .map((node) => ({
        tag: node.tagName.toLowerCase(),
        className: String(node.className).slice(0, 90),
      }));

    // Colour-only risk: a state class with no text, no aria and no icon.
    const colourOnlyStatusNodes = Array.from(
      document.querySelectorAll(
        "[class*='is-ok'],[class*='is-warn'],[class*='is-bad'],[class*='success'],[class*='danger'],[class*='warning'],[class*='ok'],[class*='warn']",
      ),
    )
      .filter((node) => {
        const own = (node.innerText || "").trim();
        const aria = node.getAttribute("aria-label") || "";
        const svg = node.querySelector("svg");
        const title = node.getAttribute("title") || "";
        return own.length === 0 && aria.length === 0 && !svg && title.length === 0;
      })
      .slice(0, 12)
      .map((node) => String(node.className).slice(0, 90));

    const clippedText = Array.from(document.querySelectorAll("h1,h2,h3,p,span,button,a,li"))
      .filter((node) => node.scrollWidth > node.clientWidth + 2 && node.clientWidth > 0)
      .slice(0, 12)
      .map((node) => ({
        tag: node.tagName.toLowerCase(),
        text: (node.innerText || "").trim().slice(0, 40),
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
      }));

    const unlabelledControls = Array.from(
      document.querySelectorAll("button,input,select,textarea,a[href]"),
    )
      .filter((node) => {
        const own = (node.innerText || "").trim();
        const aria =
          node.getAttribute("aria-label") || node.getAttribute("aria-labelledby") || "";
        const title = node.getAttribute("title") || "";
        const img = node.querySelector("img[alt]");
        return own.length === 0 && aria.length === 0 && title.length === 0 && !img;
      })
      .slice(0, 12)
      .map((node) => `${node.tagName.toLowerCase()}[${String(node.className).slice(0, 50)}]`);

    return {
      textLength: text.length,
      overflow: {
        scrollWidth: doc.scrollWidth,
        clientWidth: doc.clientWidth,
        horizontalOverflow: doc.scrollWidth > doc.clientWidth + 1,
      },
      capabilityMatches: matches,
      capabilityVocabularyFound: Object.entries(matches)
        .filter(([, hit]) => hit)
        .map(([key]) => key),
      statusChipCount: chips.length,
      namelessStatusNodes,
      colourOnlyStatusNodes,
      clippedText,
      unlabelledControls,
      reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    };
  }, patterns);
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    channel: "chrome",
    proxy: { server: "direct://" },
    args: ["--no-proxy-server", "--proxy-bypass-list=<-loopback>"],
  });

  const bootstrap = await bootstrapJourney(browser);
  writeFileSync(
    join(ROOT, "evidence", "web_mobile_bootstrap.json"),
    JSON.stringify(bootstrap, null, 1),
    "utf-8",
  );
  if (!bootstrap.seeded) {
    throw new Error(`bootstrap: journey selection did not take effect (${bootstrap.sample})`);
  }

  for (const viewport of VIEWPORTS) {
    for (const reduced of [false, true]) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        deviceScaleFactor: 1,
        isMobile: viewport.mobile,
        hasTouch: viewport.mobile,
        reducedMotion: reduced ? "reduce" : "no-preference",
        storageState: bootstrap.state,
      });
      const page = await context.newPage();
      const consoleErrors = [];
      const pageErrors = [];
      page.on("console", (m) => {
        if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200));
      });
      page.on("pageerror", (e) => pageErrors.push(String(e).slice(0, 200)));

      for (const route of ROUTES) {
        const url = `${BASE}/v8/${route}`;
        const record = { viewport: viewport.name, route, reducedMotion: reduced, url };
        try {
          await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
          await page.waitForTimeout(3000);
          record.analysis = await analyse(page, CAPABILITY_PATTERNS);
          record.title = await page.title();
          const shot = join(SHOTS, `${viewport.name}${reduced ? "-reduced" : ""}-${route}.png`);
          await page.screenshot({ path: shot, fullPage: false });
          record.screenshot = shot;
          record.ok = true;
        } catch (error) {
          record.ok = false;
          record.error = String(error).slice(0, 300);
        }
        record.consoleErrors = consoleErrors.slice(0, 6);
        record.pageErrors = pageErrors.slice(0, 6);
        consoleErrors.length = 0;
        pageErrors.length = 0;
        results.push(record);
        writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 1), "utf-8");
      }
      await context.close();
    }
  }

  // ---- keyboard focus order on the primary mobile route -------------------
  const focusContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    storageState: bootstrap.state,
  });
  const focusPage = await focusContext.newPage();
  await focusPage.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded" });
  await focusPage.waitForTimeout(3000);
  const focusOrder = [];
  for (let index = 0; index < 16; index += 1) {
    await focusPage.keyboard.press("Tab");
    focusOrder.push(
      await focusPage.evaluate(() => {
        const el = document.activeElement;
        if (!el) return null;
        const style = window.getComputedStyle(el);
        return {
          tag: el.tagName.toLowerCase(),
          text: (el.innerText || el.value || "").trim().slice(0, 40),
          aria: el.getAttribute("aria-label") || "",
          outlineStyle: style.outlineStyle,
          outlineWidth: style.outlineWidth,
          boxShadow: style.boxShadow === "none" ? "" : "present",
          visibleFocus: style.outlineStyle !== "none" || style.boxShadow !== "none",
        };
      }),
    );
  }
  writeFileSync(
    FOCUS_PATH,
    JSON.stringify(
      {
        focusOrder,
        focusable: focusOrder.filter(Boolean).length,
        withoutVisibleFocus: focusOrder.filter((f) => f && !f.visibleFocus).length,
      },
      null,
      1,
    ),
    "utf-8",
  );

  // ---- 200% zoom (CSS pixel viewport halved) ------------------------------
  const zoomContext = await browser.newContext({
    viewport: { width: 640, height: 360 },
    deviceScaleFactor: 2,
    isMobile: false,
    storageState: bootstrap.state,
  });
  const zoomPage = await zoomContext.newPage();
  const zoom = [];
  for (const route of ROUTES) {
    await zoomPage.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded" });
    await zoomPage.waitForTimeout(2500);
    const analysis = await analyse(zoomPage, CAPABILITY_PATTERNS);
    zoom.push({ route, horizontalOverflow: analysis.overflow.horizontalOverflow,
                scrollWidth: analysis.overflow.scrollWidth,
                clientWidth: analysis.overflow.clientWidth });
  }
  writeFileSync(
    join(ROOT, "evidence", "web_mobile_zoom200.json"),
    JSON.stringify(zoom, null, 1),
    "utf-8",
  );
  await zoomContext.close();
  await focusContext.close();

  // ---- capability-state probe --------------------------------------------
  // Declare a HARD accessibility need with NO evidence, then ask the UI to
  // show it.  The API now carries capability data (Snapshot B); does the UI?
  const capabilityProbe = { journeyId: bootstrap.journeyId, steps: [] };
  if (bootstrap.journeyId) {
    const jid = bootstrap.journeyId;
    capabilityProbe.steps.push({ step: "clear", ...(await api(`/api/v1/journeys/${jid}/capabilities/confirm`, { method: "POST", body: [] })) });
    capabilityProbe.steps.push({
      step: "declare_hard_unknown_evidence",
      ...(await api(`/api/v1/journeys/${jid}/capabilities/confirm`, {
        method: "POST",
        body: [{ code: "STEP_FREE_REQUIRED", severity: "HARD", params: {} }],
      })),
    });

    const probeContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
      isMobile: true,
      hasTouch: true,
      storageState: bootstrap.state,
    });
    const probePage = await probeContext.newPage();
    const perRoute = {};
    for (const route of ROUTES) {
      await probePage.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded" });
      await probePage.waitForTimeout(2500);
      const analysis = await analyse(probePage, CAPABILITY_PATTERNS);
      perRoute[route] = {
        text: (await probePage.evaluate(() => document.body.innerText)).slice(0, 700),
        capabilityVocabularyFound: analysis.capabilityVocabularyFound,
      };
      await probePage.screenshot({
        path: join(SHOTS, `capability-probe-390x844-${route}.png`),
      });
    }
    capabilityProbe.perRoute = perRoute;
    capabilityProbe.anyRouteShowsCapability = Object.values(perRoute).some(
      (r) => r.capabilityVocabularyFound.length > 0,
    );
    capabilityProbe.anyRouteShowsEvidenceState = Object.values(perRoute).some((r) =>
      /unknown|unverified|needs evidence|verified|conflict/i.test(r.text),
    );
    await probeContext.close();
    await api(`/api/v1/journeys/${jid}/capabilities/confirm`, { method: "POST", body: [] });
  }
  writeFileSync(CAPABILITY_PATH, JSON.stringify(capabilityProbe, null, 1), "utf-8");

  await browser.close();

  const summary = {
    cells: results.length,
    loaded: results.filter((r) => r.ok).length,
    screenshots: results.filter((r) => r.screenshot).length,
    distinctScreens: new Set(results.filter((r) => r.ok).map((r) => (r.analysis ? r.analysis.textLength : 0))).size,
    horizontalOverflowCells: results.filter((r) => r.ok && r.analysis?.overflow.horizontalOverflow).length,
    cellsWithCapabilityVocabulary: results.filter(
      (r) => r.ok && (r.analysis?.capabilityVocabularyFound?.length || 0) > 0,
    ).length,
    namelessStatusNodes: results.reduce((n, r) => n + (r.analysis?.namelessStatusNodes?.length || 0), 0),
    colourOnlyStatusNodes: results.reduce((r2, r) => r2 + (r.analysis?.colourOnlyStatusNodes?.length || 0), 0),
    clippedTextNodes: results.reduce((n, r) => n + (r.analysis?.clippedText?.length || 0), 0),
    unlabelledControls: results.reduce((n, r) => n + (r.analysis?.unlabelledControls?.length || 0), 0),
    pageErrors: results.reduce((n, r) => n + (r.pageErrors?.length || 0), 0),
    capabilityProbeAnyRouteShowsCapability: capabilityProbe.anyRouteShowsCapability,
    capabilityProbeAnyRouteShowsEvidenceState: capabilityProbe.anyRouteShowsEvidenceState,
  };
  writeFileSync(join(ROOT, "evidence", "web_mobile_summary.json"), JSON.stringify(summary, null, 1), "utf-8");
  console.log(JSON.stringify(summary, null, 1));
}

await run();

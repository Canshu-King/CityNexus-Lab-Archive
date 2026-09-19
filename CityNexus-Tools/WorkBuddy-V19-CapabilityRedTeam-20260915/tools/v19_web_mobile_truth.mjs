/**
 * V19 web/mobile capability-truth and accessibility review.
 *
 * Drives the isolated Vite build on 127.0.0.1:4193 (proxying /api/v1 to the
 * isolated backend on 8040) with system Chrome at the four mandated viewports.
 *
 * IMPORTANT: /v8/<route> renders the onboarding form until a journey is
 * selected, so a bootstrap context clicks "Use the sealed Tianjin demo" first
 * and its storageState is reused by every measurement context.  Without this
 * step every route renders the same onboarding screen and the review measures
 * nothing.
 */

import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = "D:/moodle/CityNexus-Tools/WorkBuddy-V19-CapabilityRedTeam-20260915";
const require = createRequire(join(ROOT, "repo_copy", "frontend", "package.json"));
const { chromium } = require("@playwright/test");

const BASE = "http://127.0.0.1:4193";
const SHOTS = join(ROOT, "evidence", "screenshots");
mkdirSync(SHOTS, { recursive: true });

const VIEWPORTS = [
  { name: "mobile-390x844", width: 390, height: 844, mobile: true },
  { name: "mobile-430x932", width: 430, height: 932, mobile: true },
  { name: "desktop-1280x720", width: 1280, height: 720, mobile: false },
  { name: "desktop-1440x900", width: 1440, height: 900, mobile: false },
];

const ROUTES = ["hub", "live", "map", "studio", "bookings", "agent", "authoritative", "twin"];

const CAPABILITY_PATTERNS = [
  "capability",
  "step-free",
  "step_free",
  "accessib",
  "wheelchair",
  "stroller",
  "unknown evidence",
  "needs evidence",
  "verified",
];

const results = [];

/**
 * Seed the sealed demo journey and return the storageState that carries the
 * journey selection into every measurement context.
 */
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
  await page.waitForTimeout(7000);

  const text = await page.evaluate(() => document.body.innerText);
  const seeded = text.includes("Journey Hub") && !text.includes("Start a real");
  const state = await context.storageState();
  await context.close();
  return { state, seeded, sample: text.slice(0, 200).replace(/\s+/g, " ") };
}

async function analyse(page) {
  return page.evaluate(
    (patterns) => {
      const text = document.body ? document.body.innerText || "" : "";
      const lower = text.toLowerCase();
      const doc = document.documentElement;
      const overflow = {
        scrollWidth: doc.scrollWidth,
        clientWidth: doc.clientWidth,
        horizontalOverflow: doc.scrollWidth > doc.clientWidth + 1,
      };
      const matches = {};
      for (const pattern of patterns) {
        matches[pattern] = lower.includes(pattern);
      }
      // status-like chips that carry no text and no accessible name
      const chips = Array.from(
        document.querySelectorAll(
          "[class*='chip'],[class*='badge'],[class*='pill'],[class*='status'],[class*='state']",
        ),
      );
      const nameless = chips
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
      // colour-only risk: a state class whose element has neither text nor icon nor aria
      const colourOnly = Array.from(
        document.querySelectorAll("[class*='is-ok'],[class*='is-warn'],[class*='is-bad'],[class*='success'],[class*='danger'],[class*='warning']"),
      )
        .filter((node) => {
          const own = (node.innerText || "").trim();
          const aria = node.getAttribute("aria-label") || "";
          const svg = node.querySelector("svg");
          return own.length === 0 && aria.length === 0 && !svg;
        })
        .slice(0, 12)
        .map((node) => String(node.className).slice(0, 90));
      // clipped text: an element whose own scrollWidth exceeds clientWidth
      const clipped = Array.from(document.querySelectorAll("h1,h2,h3,p,span,button,a,li"))
        .filter((node) => node.scrollWidth > node.clientWidth + 2 && node.clientWidth > 0)
        .slice(0, 12)
        .map((node) => ({
          tag: node.tagName.toLowerCase(),
          text: (node.innerText || "").trim().slice(0, 40),
          scrollWidth: node.scrollWidth,
          clientWidth: node.clientWidth,
        }));
      const unlabelledControls = Array.from(document.querySelectorAll("button,input,select,textarea,a[href]"))
        .filter((node) => {
          const own = (node.innerText || "").trim();
          const aria = node.getAttribute("aria-label") || node.getAttribute("aria-labelledby") || "";
          const title = node.getAttribute("title") || "";
          const img = node.querySelector("img[alt]");
          return own.length === 0 && aria.length === 0 && title.length === 0 && !img;
        })
        .slice(0, 12)
        .map((node) => `${node.tagName.toLowerCase()}[${String(node.className).slice(0, 50)}]`);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      return {
        textLength: text.length,
        overflow,
        capabilityMatches: matches,
        namelessStatusNodes: nameless,
        colourOnlyStatusNodes: colourOnly,
        clippedText: clipped,
        unlabelledControls,
        reducedMotion,
        statusChipCount: chips.length,
      };
    },
    CAPABILITY_PATTERNS,
  );
}

async function run() {
  // The host runs a system proxy (U1S1 Cloud on 127.0.0.1:7892).  Chrome would
  // otherwise route the loopback requests through it, which returns 502 or
  // hangs.  Force a direct connection for the whole browser.
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
      page.on("console", (message) => {
        if (message.type() === "error") consoleErrors.push(message.text().slice(0, 200));
      });
      page.on("pageerror", (error) => pageErrors.push(String(error).slice(0, 200)));

      for (const route of ROUTES) {
        const url = `${BASE}/v8/${route}`;
        const record = { viewport: viewport.name, route, reducedMotion: reduced, url };
        try {
          await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
          await page.waitForTimeout(3000);
          const analysis = await analyse(page);
          record.analysis = analysis;
          record.title = await page.title();
          const shot = join(
            SHOTS,
            `${viewport.name}${reduced ? "-reduced" : ""}-${route}.png`,
          );
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
        // Flush after every record so a watchdog kill still leaves usable evidence.
        writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 1), "utf-8");
      }
      await context.close();
    }
  }

  // keyboard + focus visibility probe on the primary mobile route
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    storageState: bootstrap.state,
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  const focusOrder = [];
  for (let index = 0; index < 14; index += 1) {
    await page.keyboard.press("Tab");
    const info = await page.evaluate(() => {
      const active = document.activeElement;
      if (!active) return null;
      const style = window.getComputedStyle(active);
      const rect = active.getBoundingClientRect();
      return {
        tag: active.tagName.toLowerCase(),
        name:
          (active.getAttribute("aria-label") || active.innerText || active.getAttribute("title") || "")
            .trim()
            .slice(0, 44),
        outlineWidth: style.outlineWidth,
        outlineStyle: style.outlineStyle,
        boxShadow: style.boxShadow.slice(0, 40),
        visible: rect.width > 0 && rect.height > 0,
      };
    });
    if (info) focusOrder.push(info);
  }
  const axe = await runAxe(page);
  const axeByRoute = {};
  for (const route of ["live", "studio", "bookings", "twin", "agent"]) {
    await page.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    axeByRoute[route] = await runAxe(page);
  }
  writeFileSync(
    join(ROOT, "evidence", "web_mobile_focus_and_axe.json"),
    JSON.stringify({ focusOrder, axe, axeByRoute }, null, 1),
    "utf-8",
  );
  await context.close();
  await browser.close();

  writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 1), "utf-8");
  console.log(`records=${results.length}`);
}

async function runAxe(page) {
  try {
    const axeSource = require.resolve("axe-core/axe.min.js");
    await page.addScriptTag({ path: axeSource });
    const result = await page.evaluate(async () => {
      // eslint-disable-next-line no-undef
      return await window.axe.run(document, {
        resultTypes: ["violations"],
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] },
      });
    });
    return {
      violationCount: result.violations.length,
      violations: result.violations.map((item) => ({
        id: item.id,
        impact: item.impact,
        nodes: item.nodes.length,
        help: item.help,
        sample: String(item.nodes[0]?.html || "").slice(0, 140),
      })),
    };
  } catch (error) {
    return { error: String(error).slice(0, 300) };
  }
}

const WATCHDOG_MS = 9 * 60 * 1000;
const RESULTS_PATH = join(ROOT, "evidence", "web_mobile_results.json");

setTimeout(() => {
  writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 1), "utf-8");
  console.error(`WATCHDOG: flushed ${results.length} partial records after ${WATCHDOG_MS} ms`);
  process.exit(2);
}, WATCHDOG_MS).unref();

run().catch((error) => {
  console.error("FATAL", error);
  process.exitCode = 1;
});

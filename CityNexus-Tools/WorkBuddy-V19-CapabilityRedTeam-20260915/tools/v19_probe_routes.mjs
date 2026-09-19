// Exploration: how do we actually reach the eight v8 route surfaces?
// Run: node tools/v19_probe_routes.mjs
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = "D:/moodle/CityNexus-Tools/WorkBuddy-V19-CapabilityRedTeam-20260915";
const require = createRequire(join(ROOT, "repo_copy", "frontend", "package.json"));
const { chromium } = require("@playwright/test");
const BASE = "http://127.0.0.1:4193";
const ROUTES = ["hub", "live", "map", "studio", "bookings", "agent", "authoritative", "twin"];

const out = {};

const browser = await chromium.launch({
  headless: true,
  channel: "chrome",
  proxy: { server: "direct://" },
  args: ["--no-proxy-server", "--proxy-bypass-list=<-loopback>"],
});
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();

const consoleErrors = [];
page.on("console", (m) => {
  if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200));
});
page.on("pageerror", (e) => consoleErrors.push("PAGEERROR " + String(e).slice(0, 200)));

await page.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded", timeout: 20000 });
await page.waitForTimeout(2500);

out.beforeClick = {
  url: page.url(),
  bodyText: (await page.evaluate(() => document.body.innerText)).slice(0, 400),
  buttons: await page.evaluate(() =>
    [...document.querySelectorAll("button")].map((b) => (b.innerText || b.getAttribute("aria-label") || "").trim()).slice(0, 20),
  ),
  links: await page.evaluate(() =>
    [...document.querySelectorAll("a")].map((a) => ({ text: (a.innerText || "").trim().slice(0, 40), href: a.getAttribute("href") })).slice(0, 20),
  ),
};

// Click the sealed demo button if present.
const demo = page.getByRole("button", { name: /sealed Tianjin demo|Tianjin demo/i });
if (await demo.count()) {
  await demo.first().click();
  await page.waitForTimeout(6000);
}
out.afterClick = {
  url: page.url(),
  bodyText: (await page.evaluate(() => document.body.innerText)).slice(0, 600),
  buttons: await page.evaluate(() =>
    [...document.querySelectorAll("button")].map((b) => (b.innerText || b.getAttribute("aria-label") || "").trim()).slice(0, 25),
  ),
  links: await page.evaluate(() =>
    [...document.querySelectorAll("a")].map((a) => ({ text: (a.innerText || "").trim().slice(0, 40), href: a.getAttribute("href") })).slice(0, 25),
  ),
};

// Now try each route again with the journey in place.
out.routes = {};
for (const route of ROUTES) {
  await page.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.waitForTimeout(3000);
  const text = await page.evaluate(() => document.body.innerText);
  out.routes[route] = {
    url: page.url(),
    textLength: text.length,
    head: text.slice(0, 260).replace(/\s+/g, " "),
    inputs: await page.evaluate(() => document.querySelectorAll("input").length),
    statusChips: await page.evaluate(
      () => document.querySelectorAll('[class*="chip"],[class*="status"],[class*="badge"]').length,
    ),
  };
}

out.consoleErrors = consoleErrors.slice(0, 20);
await browser.close();
writeFileSync(join(ROOT, "evidence", "route_probe.json"), JSON.stringify(out, null, 1), "utf-8");
console.log(JSON.stringify(out, null, 1).slice(0, 4000));

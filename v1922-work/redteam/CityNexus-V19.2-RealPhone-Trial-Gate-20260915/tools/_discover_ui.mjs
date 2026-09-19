/**
 * Quick discovery: what does the V19.1 frontend actually render, and what is the
 * demo-seeding control called?
 */
import { createRequire } from "node:module";
import { join } from "node:path";

const ROOT = "D:/moodle/CityNexus-Tools/WorkBuddy-V19.1-ConvergenceRedTeam-20260915";
const require = createRequire(join(ROOT, "snapshot_b", "frontend", "package.json"));
const { chromium } = require("@playwright/test");

const BASE = "http://127.0.0.1:4203";

const browser = await chromium.launch({
  headless: true,
  channel: "chrome",
  proxy: { server: "direct://" },
  args: ["--no-proxy-server", "--proxy-bypass-list=<-loopback>"],
});
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();
page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0, 200)));
page.on("console", (m) => {
  if (m.type() === "error") console.log("CONSOLE:", m.text().slice(0, 200));
});

await page.goto(`${BASE}/v8/hub`, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.waitForTimeout(4000);
console.log("TITLE:", await page.title());
console.log("URL:", page.url());
const text = await page.evaluate(() => document.body.innerText);
console.log("TEXT (first 1200):\n", text.slice(0, 1200));

const buttons = await page.evaluate(() =>
  Array.from(document.querySelectorAll("button")).map((b) => ({
    text: (b.innerText || "").trim().slice(0, 60),
    aria: b.getAttribute("aria-label") || "",
  })),
);
console.log("BUTTONS:", JSON.stringify(buttons, null, 1).slice(0, 1500));

console.log("localStorage:", await page.evaluate(() => JSON.stringify(Object.entries(localStorage))));

await browser.close();

/**
 * Capture the same-Xiamen flow at the three acceptance viewports.
 * Xiaomi 13 Ultra is 3200x1440 physical, DPR 3.5 -> 412x915 CSS.
 */
const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const EV = "D:/moodle/_v1922_work/o2_evidence";
const SHOTS = EV + "/shots";
const J = JSON.parse(fs.readFileSync(EV + "/scenario_degraded.json", "utf8")).journey_id;
const VIEWPORTS = [
  { name: "390x844", width: 390, height: 844, dpr: 2 },
  { name: "430x932", width: 430, height: 932, dpr: 3 },
  { name: "xiaomi13ultra-412x915", width: 412, height: 915, dpr: 3.5 },
];
const ROUTES = [
  { path: "/v8/hub", name: "today" },
  { path: "/v8/trips", name: "trips" },
  { path: "/v8/map", name: "map" },
  { path: "/v8/live", name: "live" },
  { path: "/v8/me", name: "me" },
];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const out = [];
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.dpr, isMobile: true, hasTouch: true, locale: "zh-CN",
    });
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e).slice(0, 120)));
    await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
    for (const r of ROUTES) {
      await page.goto(BASE + r.path, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${SHOTS}/vp_${vp.name}_${r.name}.png` });
      const text = (await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 90);
      out.push({ viewport: vp.name, route: r.path, chars: text.length, sample: text });
    }
    // Copilot dock open state at this width.
    await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await page.locator(".cn-copilot-edge").click().catch(() => {});
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${SHOTS}/vp_${vp.name}_copilot.png` });
    out.push({ viewport: vp.name, route: "/v8/agent(dock-open)", chars: 1, sample: "dock open" });
    fs.writeFileSync(`${EV}/viewports_${vp.name}.json`, JSON.stringify({ viewport: vp, screens: out, errors }, null, 1));
    await ctx.close();
  }
  fs.writeFileSync(`${EV}/VIEWPORT_EVIDENCE.json`, JSON.stringify(out, null, 1));
  out.forEach((o) => console.log(`${o.viewport.padEnd(26)} ${o.route.padEnd(24)} ${o.chars} ${o.sample.slice(0, 60)}`));
  await browser.close();
})();

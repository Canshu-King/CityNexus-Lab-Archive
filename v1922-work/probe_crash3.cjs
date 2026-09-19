const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 3.5, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  let crashed = false;
  page.on("crash", () => { crashed = true; console.log("CRASH"); });
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,200)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE", m.text().slice(0,180)); });
  const step = async (label, fn) => {
    if (crashed) { console.log("skip", label); return; }
    try { await fn(); await page.waitForTimeout(1500); console.log("ok", label, "crashed=", crashed); }
    catch (e) { console.log("FAIL", label, String(e).slice(0,110)); }
  };
  await step("goto /", () => page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded", timeout: 60000 }));
  await step("wait", () => page.waitForTimeout(2500));
  await step("city", () => page.locator('[data-testid="trial-city"]').fill("厦门"));
  await step("arrival", () => page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场"));
  await step("departure", () => page.locator('[data-testid="trial-departure"]').fill("厦门北站"));
  await step("start", () => page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00"));
  await step("end", () => page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00"));
  await step("next1", () => page.locator('[data-testid="trial-next"]').click());
  await step("budget", () => page.locator('[data-testid="trial-budget"]').fill("3000"));
  await step("staybudget", () => page.locator('[data-testid="trial-stay-budget"]').fill("1000"));
  await step("next2", () => page.locator('[data-testid="trial-next"]').click());
  await step("create", () => page.locator('[data-testid="trial-create"]').click());
  await step("settle", () => page.waitForTimeout(9000));
  console.log("JID:", await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id")).catch(()=>"<err>"));
  await browser.close();
})();

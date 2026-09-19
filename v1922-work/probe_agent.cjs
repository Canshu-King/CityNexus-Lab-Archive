const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("crash", () => console.log("PAGE CRASHED"));
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,150)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE", m.text().slice(0,150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  for (const r of ["/v8/agent", "/v8/map", "/v8/live"]) {
    try {
      await page.goto("http://127.0.0.1:5173" + r, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(6000);
      const t = (await page.locator("body").innerText()).replace(/\n+/g," | ").slice(0,180);
      console.log("OK", r, "|", t);
      await page.screenshot({ path: `D:/moodle/_v1922_work/o2_evidence/shots/probe${r.replace(/\//g,"_")}.png` });
    } catch (e) { console.log("FAIL", r, String(e).slice(0,200)); }
  }
  await browser.close();
})();

const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8").match(/"([0-9a-f-]{36})"/)[1];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,250)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE:", m.text().slice(0,250)); });
  page.on("response", async (r) => {
    if (/stay-options|stays\/offers|experience/.test(r.url())) {
      console.log("RESP", r.status(), r.request().method(), r.url().split("/api/v1")[1]);
    }
  });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  console.log("journey", J);
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  for (let i=0;i<8;i++){
    await page.waitForTimeout(5000);
    const cards = await page.locator('[data-testid="hotel-card"]').count();
    const empty = await page.locator('[data-testid="hotels-empty"]').count();
    console.log(i, "cards=", cards, "empty=", empty);
    if (cards) break;
  }
  console.log("PANEL:", (await page.locator('[data-testid="hotels-panel"]').innerText().catch(()=>"<none>")).replace(/\n+/g," | ").slice(0,300));
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_hotels2.png" });
  await browser.close();
})();

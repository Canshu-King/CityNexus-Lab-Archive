const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,200)));
  page.on("response", async (r) => {
    if (/plans|select/.test(r.url())) {
      const t = await r.text().catch(()=> "");
      console.log("RESP", r.status(), r.request().method(), r.url().replace("http://127.0.0.1:5173",""), t.slice(0,220));
    }
  });
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE", m.text().slice(0,200)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(6000);
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  console.log("cards:", cards);
  if (cards) {
    const btn = page.locator('[data-testid="plan-cmp-choose"]').first();
    console.log("btn text:", (await btn.innerText().catch(()=>"")).slice(0,60), "disabled:", await btn.isDisabled().catch(()=>"?"));
    await btn.click();
    await page.waitForTimeout(9000);
    console.log("after click, comparison still there:", await page.locator('[data-testid="plan-comparison"]').count());
    console.log("error text:", (await page.locator('[data-testid="plan-cmp-error"]').innerText().catch(()=>"<none>")).slice(0,200));
    console.log("body:", (await page.locator("body").innerText()).replace(/\n+/g," | ").slice(0,300));
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_choose.png", fullPage: true });
  await browser.close();
})();

const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/scenario_hostile.json","utf8")).journey_id;
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,200)));
  page.on("response", async (r) => {
    if (/stay-options|stays\/offers|experience/.test(r.url())) {
      let n=""; try { const b=await r.json(); n="offers="+((b.offers||[]).length)+" options="+((b.options||b.top_k||[]).length); } catch {}
      console.log("RESP", r.status(), r.request().method(), r.url().split("/api/v1")[1].split("?")[0], n);
    }
  });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  console.log("journey", J);
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  for (let i=0;i<14;i++){
    await page.waitForTimeout(5000);
    console.log(i, "cards=", await page.locator('[data-testid="hotel-card"]').count(), "empty=", await page.locator('[data-testid="hotels-empty"]').count());
  }
  console.log("PANEL:", (await page.locator('[data-testid="hotels-panel"]').innerText().catch(()=>"<none>")).replace(/\n+/g," | ").slice(0,260));
  await browser.close();
})();

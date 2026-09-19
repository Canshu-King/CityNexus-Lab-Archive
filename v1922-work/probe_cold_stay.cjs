const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,200)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE:", m.text().slice(0,200)); });
  const seen = [];
  page.on("response", async (r) => {
    if (/stay-options|stays\/offers|experience|plans/.test(r.url())) {
      let n = "";
      try { const b = await r.json();
        n = "offers=" + ((b.offers||[]).length) + " options=" + ((b.options||b.top_k||[]).length) + " plans=" + ((b||[]).length);
      } catch {}
      const line = `${r.status()} ${r.request().method()} ${r.url().split("/api/v1")[1].split("?")[0]} ${n}`;
      seen.push(line); console.log("RESP", line);
    }
  });
  // Fresh journey through the real wizard.
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-create"]').click(); await page.waitForTimeout(8000);
  const J = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
  console.log("JOURNEY", J);
  // Create + select a plan through the UI so the journey has an active plan.
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(()=>{});
  await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  for (let i=0;i<40;i++){ await page.waitForTimeout(3000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(()=>null);
    if (n !== null) { console.log("AI plan count:", n); break; } }
  await page.locator(".plan-ai-close").click().catch(()=>{});
  await page.waitForTimeout(2000);
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  await page.locator('[data-testid="plan-cmp-choose"]').first().click();
  for (let i=0;i<25;i++){ await page.waitForTimeout(2000);
    if (!(await page.locator('[data-testid="plan-comparison"]').count())) break; }
  console.log("plan selected");
  // Now the COLD stay tab: options do not exist yet.
  await page.goto("http://127.0.0.1:5173/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  for (let i=0;i<20;i++){
    await page.waitForTimeout(5000);
    const cards = await page.locator('[data-testid="hotel-card"]').count();
    const empty = await page.locator('[data-testid="hotels-empty"]').count();
    console.log(i, "cards=", cards, "empty=", empty);
    if (cards) break;
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_cold_stay.png" });
  console.log("PANEL:", (await page.locator('[data-testid="hotels-panel"]').innerText().catch(()=>"<none>")).replace(/\n+/g," | ").slice(0,200));
  await browser.close();
})();

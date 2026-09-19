const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,150)));
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
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
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="hub-plan-with-ai"]').click().catch(()=>{});
  await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  for (let i=0;i<60;i++){ await page.waitForTimeout(2500);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(()=>null);
    if (n !== null) break; }
  await page.locator(".plan-ai-close").click().catch(()=>{});
  await page.waitForTimeout(2000);
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const n = await page.locator('[data-testid="plan-cmp-card"]').count();
  console.log("cards:", n);
  for (let i=0;i<n;i++){
    const band = await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(()=>"?");
    const card = await page.locator('[data-testid="plan-cmp-card"]').nth(i).innerText().catch(()=>"");
    console.log(i, "band=", band.trim(), "|", card.replace(/\n+/g," | ").slice(0,120));
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_budget2.png" });
  await browser.close();
})();

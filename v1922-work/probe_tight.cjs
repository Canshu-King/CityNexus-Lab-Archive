const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", String(e).slice(0,140)));
  // 39-day / 2-person / CNY 3000 journey through the real wizard
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-01T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-12-09T20:00");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(700);
  await page.locator('[data-testid="trial-create"]').click(); await page.waitForTimeout(9000);
  await page.goto("http://127.0.0.1:5173/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const adv = await page.locator('[data-testid="budget-advisory"]');
  console.log("present:", await adv.count(), "| tight:", await adv.getAttribute("data-tight").catch(()=>"?"));
  console.log("TEXT:", (await adv.innerText().catch(()=>"<none>")).replace(/\s+/g," ").slice(0,220));
  console.log("edit button:", await page.locator('[data-testid="budget-advisory-edit"]').count(),
              "| continue:", await page.locator('[data-testid="budget-advisory-continue"]').count());
  await page.locator('[data-testid="budget-advisory-continue"]').click().catch(()=>{});
  await page.waitForTimeout(1200);
  console.log("after continue, dismissed:", (await page.locator('[data-testid="budget-advisory"]').count()) === 0);
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/hotfix_budget_tight.png" });
  await browser.close();
})();

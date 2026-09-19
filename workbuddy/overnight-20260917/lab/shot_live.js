// Live-compare shot: EAC's running dev server (READ-ONLY, GET navigation only)
const { chromium } = require("playwright-core");
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe", headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  await page.goto("http://localhost:5173/v8/hub", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(4000);
  await page.screenshot({ path: OUT + "\\eac_live_hub_390x844.png" });
  console.log("ok " + page.url());
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

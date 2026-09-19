const { chromium } = require("playwright-core");
const fs = require("fs");
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe", headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => localStorage.setItem("citynexus.v8.journey_id", "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9"));
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  await page.screenshot({ path: OUT + "\\probe_hub_now.png" });
  const t = await page.locator("body").innerText().catch(() => "");
  fs.writeFileSync(OUT + "\\probe_hub_now_text.txt", t.slice(0, 2500), "utf8");
  console.log(t.slice(0, 600).replace(/\n+/g, " | "));
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

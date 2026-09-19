// Re-enter with the already-created journey id (no new creation): verify boot path
const { chromium } = require("playwright-core");
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe", headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => localStorage.setItem("citynexus.v8.journey_id", "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9"));
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  await page.screenshot({ path: OUT + "\\flow_05_reenter_hub.png" });
  const text = (await page.locator("body").innerText().catch(() => "")).slice(0, 1500);
  require("fs").writeFileSync(OUT + "\\flow_05_reenter_hub_text.txt", text, "utf8");
  // tabs
  for (const route of ["trips", "map", "agent", "me"]) {
    await page.goto("http://localhost:5181/v8/" + route, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3500);
    await page.screenshot({ path: OUT + "\\flow_05_tab_" + route + ".png" });
  }
  console.log("done");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

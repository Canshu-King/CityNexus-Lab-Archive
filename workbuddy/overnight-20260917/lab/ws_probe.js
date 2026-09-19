// Systematic white-screen probe: fresh context vs journey context, full error capture
const { chromium } = require("playwright-core");
const fs = require("fs");
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
async function runCase(browser, label, withJourney) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errs = [];
  page.on("console", (m) => errs.push(`[console.${m.type()}] ${m.text().slice(0, 300)}`));
  page.on("pageerror", (e) => errs.push(`[pageerror] ${e.message} || stack: ${String(e.stack).slice(0, 400)}`));
  page.on("requestfailed", (r) => errs.push(`[reqfail] ${r.url().slice(0, 120)} :: ${r.failure()?.errorText}`));
  page.on("response", (r) => { if (r.status() >= 400) errs.push(`[HTTP ${r.status()}] ${r.url().slice(0, 140)}`); });
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  if (withJourney) await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(9000);
  const rootChildren = await page.evaluate(() => document.getElementById("root")?.children.length ?? -1);
  const shot = OUT + `\\ws_${label}.png`;
  await page.screenshot({ path: shot });
  const res = { label, withJourney, rootChildren, errors: errs.slice(0, 25), shot };
  console.log(JSON.stringify(res, null, 1));
  await ctx.close();
  return res;
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe", headless: true });
  const a = await runCase(browser, "fresh_no_journey", false);
  const b = await runCase(browser, "with_journey", true);
  fs.writeFileSync(OUT + "\\ws_matrix.json", JSON.stringify([a, b], null, 2), "utf8");
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

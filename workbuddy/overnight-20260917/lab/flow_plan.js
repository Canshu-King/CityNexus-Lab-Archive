// Plan comparison -> select -> trips -> activity detail chain
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const shot = async (n) => { const p = path.join(OUT, `pc_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p, url: page.url() }); };
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  // click 查看方案
  await page.getByRole("link", { name: /查看方案/ }).first().click().catch(async () => {
    await page.getByRole("button", { name: /查看方案/ }).first().click();
  });
  await page.waitForTimeout(4000);
  await shot("00_plan_view");
  const t0 = (await page.locator("body").innerText().catch(() => "")).slice(0, 2600);
  fs.writeFileSync(path.join(OUT, "pc_00_plan_view_text.txt"), t0, "utf8");
  log("plan_view_text", { sample: t0.replace(/\n+/g, " | ").slice(0, 700) });
  fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\pc_trace.json", JSON.stringify(trace, null, 2), "utf8");
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

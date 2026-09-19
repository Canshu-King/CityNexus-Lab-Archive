// Offline resilience (Dexie / offline-snapshot) + Copilot replan question (TC-06)
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const shot = async (n) => { const p = path.join(OUT, `of_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  // warm online visit (populate Dexie + offline snapshot)
  await page.goto("http://localhost:5181/v8/trips", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  await shot("00_online_warm");

  // go offline, hard reload
  await ctx.setOffline(true);
  await page.goto("http://localhost:5181/v8/trips", { waitUntil: "domcontentloaded", timeout: 20000 }).catch((e) => log("offline_nav_partial", { err: String(e).slice(0, 120) }));
  await page.waitForTimeout(6000);
  await shot("01_offline_trips");
  const offText = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  log("offline_trips", { text: offText.slice(0, 600), hasOfflineBadge: /离线|OFFLINE/i.test(offText), hasReadOnly: /只读|READ ONLY/i.test(offText) });

  // try copilot offline
  const box = page.locator("textarea:visible, input[type='text']:visible").last();
  const hasBox = await box.count();
  if (hasBox) {
    await box.fill("下暴雨了，帮我调整明天的安排").catch(() => {});
    await page.getByRole("button", { name: /询问 Copilot|Ask Copilot/ }).first().click().catch(() => {});
    await page.waitForTimeout(8000);
    await shot("02_offline_copilot");
    const cpText = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
    log("offline_copilot", { text: cpText.slice(0, 600) });
  }

  // back online: ask replan question (TC-06)
  await ctx.setOffline(false);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await page.getByText("CityNexus Copilot").first().click().catch(() => {});
  await page.waitForTimeout(2000);
  const box2 = page.locator("textarea:visible, input[type='text']:visible").last();
  await box2.fill("下暴雨了，帮我调整明天的安排").catch(() => {});
  await page.getByRole("button", { name: /询问 Copilot|Ask Copilot/ }).first().click().catch((e) => log("replan_click_fail", { err: String(e).slice(0, 120) }));
  await page.waitForTimeout(20000);
  await shot("03_replan_reply");
  const rpText = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  const leaks = {};
  for (const t of ["REQUEST_REPLAN", "REPLAN", "DeepSeek", "UNVERIFIED", "PlanVersion"]) { if (rpText.includes(t)) leaks[t] = true; }
  log("replan_scan", { leaks, snippet: rpText.slice(0, 800) });

  fs.writeFileSync(path.join(EV.replace("CityNexus-WorkBuddy", "CityNexus-WorkBuddy"), "offline_replan_trace.json"), JSON.stringify(trace, null, 2), "utf8").catch(() => {});
  fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\offline_replan_trace.json", JSON.stringify(trace, null, 2), "utf8");
  await browser.close();
  log("done", {});
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\offline_fatal.txt", String(e), "utf8"); process.exit(1); });

// FINAL DELTA live test A: F9 deep links, F3 Me, F5 bookings, F1 copilot place question
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots\\final";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
fs.mkdirSync(OUT, { recursive: true });
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const BAD = ["DeepSeek", "Hermes", "Semantic:", "REQUEST_PLACE_SEARCH", "PlanVersion", "JourneyTwin", "TravelerTwin", "受保护 C4", "UNKNOWN_REALTIME", "UNVERIFIED", "DISCOVER", "STRUCTURED_JSON", "DETERMINISTIC", "ADVISORY", "CN-XIAMEN"];
const scan = async (page, label) => {
  const text = await page.locator("body").innerText().catch(() => "");
  const hits = BAD.filter((b) => text.includes(b));
  log(`LEAK[${label}]:`, hits.length ? hits.join(", ") : "clean", `(${text.length} chars)`);
  fs.writeFileSync(path.join(EV, `final_${label}_text.txt`), text.slice(0, 4000), "utf8");
  return { label, hits, chars: text.length };
};
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message.slice(0, 120)));
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `fa_${n}.png`) }); log("shot", n); };
  const R = {};

  // ---- F9: deep links without journey
  for (const r of ["today", "copilot"]) {
    await page.goto(`http://localhost:5181/v8/${r}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4500);
    const t = await page.locator("body").innerText().catch(() => "");
    R[`f9_${r}`] = { chars: t.length, useful: t.length > 200, snippet: t.slice(0, 150).replace(/\n+/g, " | ") };
    log(`F9 /v8/${r}: chars=${t.length}`);
    await shot(`f9_${r}`);
  }

  // ---- F3: Me page (no journey)
  await page.goto("http://localhost:5181/v8/me", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4500);
  R.f3_me = await scan(page, "me_nojourney");
  R.f3_advisory_visible = R.f3_me.hits.includes("ADVISORY");
  R.f3_cnxiamen_visible = R.f3_me.hits.includes("CN-XIAMEN");
  await shot("f3_me");

  // ---- F5: bookings route
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4500);
  R.f5 = await scan(page, "bookings");
  R.f5_json_textarea = await page.locator("#reservation-json").isVisible().catch(() => false);
  R.f5_advanced_labeled = /高级|开发者|Advanced|Developer/.test(await page.locator("body").innerText().catch(() => ""));
  const pre = errors.length;
  if (R.f5_json_textarea) {
    await page.locator("#reservation-json").fill("我的火车票 G1655 厦门北到福州南，明天上午 9 点发车");
    const sub = page.locator("button").filter({ hasText: /保护|审核|导入|预订/ }).first();
    await sub.click().catch(() => {});
    await page.waitForTimeout(3500);
    const after = await page.locator("body").innerText().catch(() => "");
    R.f5_feedback = /无效|格式|无法|解析|失败|请输入/.test(after);
    R.f5_pageerrors = errors.length - pre;
    log(`F5 feedback=${R.f5_feedback} pageerrors=${R.f5_pageerrors}`);
  }
  await shot("f5_bookings");

  // ---- F1: copilot place question WITH journey (post-fix code from package)
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/agent", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const ata = page.locator("textarea").last();
  if (await ata.isVisible().catch(() => false)) {
    await ata.fill("鼓浪屿好玩吗？");
    const send = page.locator("button[type=submit], form button").last();
    await send.click().catch(async () => { await ata.press("Enter"); });
    log("F1 question sent, polling...");
    const t0 = Date.now();
    while (Date.now() - t0 < 100000) {
      await page.waitForTimeout(8000);
      const t = await page.locator("body").innerText().catch(() => "");
      if ((t.match(/厦门|CityNexus/g) || []).length >= 2 && t.length > 300) break;
    }
    await page.waitForTimeout(3000);
  } else { log("F1 agent textarea NOT visible"); }
  R.f1 = await scan(page, "agent_placeq");
  await shot("f1_agent_reply");

  // ---- F2 spot: dock leakage on today with journey
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  R.f2_today = await scan(page, "today_journey");
  await shot("f2_today");

  R.pageErrors = errors.slice(0, 15);
  fs.writeFileSync(path.join(EV, "final_live_A_summary.json"), JSON.stringify(R, null, 2), "utf8");
  await browser.close();
  log("DONE-A");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

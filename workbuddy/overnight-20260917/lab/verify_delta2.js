// Delta verification round 2: H3 (agent route + dock), H5, H2, offline positive
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const BAD = ["DeepSeek", "Hermes", "Semantic:", "REQUEST_PLACE_SEARCH", "PlanVersion", "JourneyTwin", "受保护 C4", "UNKNOWN_REALTIME", "UNVERIFIED", "DISCOVER"];
const leakageScan = async (page, label) => {
  const text = await page.locator("body").innerText().catch(() => "");
  const hits = BAD.filter((b) => text.includes(b));
  log(`LEAK[${label}]:`, hits.length ? hits.join(", ") : "clean");
  return { label, hits };
};
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `dlt2_${n}.png`) }); log("shot", n); };
  const results = {};

  // journey context
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  await shot("00_today_journey");
  await leakageScan(page, "today_journey");
  const jt = await page.locator("body").innerText().catch(() => "");
  log("today_journey chars:", jt.length);
  fs.writeFileSync(path.join(EV, "delta_today_journey_text.txt"), jt.slice(0, 3000), "utf8");

  // ---- H3a: /v8/agent (AgentComposer)
  await page.goto("http://localhost:5181/v8/agent", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await shot("01_agent_page");
  const ata = page.locator("textarea").last();
  const hasTa = await ata.isVisible().catch(() => false);
  log("agent textarea:", hasTa);
  if (hasTa) {
    await ata.fill("鼓浪屿好玩吗？帮我看看");
    const send = page.locator("button[type=submit], button:has-text('发送'), button:has-text('询问')").last();
    await send.click().catch(async () => { await ata.press("Enter"); });
    log("agent question sent, polling reply...");
    const t0 = Date.now();
    while (Date.now() - t0 < 90000) {
      await page.waitForTimeout(8000);
      const t = await page.locator("body").innerText().catch(() => "");
      if (t.length > 400 && /CityNexus|回答/.test(t)) break;
    }
    await page.waitForTimeout(2000);
  }
  await shot("02_agent_reply");
  results.leak_agent = await leakageScan(page, "agent_route");

  // ---- H3b: CopilotDock via edge button on hub
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const edge = page.locator('[data-testid="v18-copilot-dock"] .cn-copilot-edge, [data-testid="v18-copilot-dock"] button').first();
  if (await edge.isVisible().catch(() => false)) {
    await edge.click();
    await page.waitForTimeout(1500);
    const dta = page.locator("textarea").last();
    if (await dta.isVisible().catch(() => false)) {
      await dta.fill("鼓浪屿好玩吗？帮我看看");
      const dsend = page.locator(".cn-copilot-panel button[type=submit], .cn-copilot-panel form button").last();
      await dsend.click().catch(async () => { await dta.press("Enter"); });
      const t0 = Date.now();
      while (Date.now() - t0 < 90000) {
        await page.waitForTimeout(8000);
        const bubbles = await page.locator(".cn-copilot-bubble").count().catch(() => 0);
        if (bubbles >= 2) break;
      }
      await page.waitForTimeout(2000);
    }
  } else { log("dock edge not visible"); }
  await shot("03_dock_reply");
  results.leak_dock = await leakageScan(page, "copilot_dock");

  // ---- H5: stay
  await page.goto("http://localhost:5181/v8/stay", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const st = await page.locator("body").innerText().catch(() => "");
  results.stay_honest_empty = /还没有可用的住宿候选|暂无供应商证据/.test(st);
  results.stay_pseudo_evidence = /0% confidence|Provider price unavailable/.test(st);
  log("H5 honest empty:", results.stay_honest_empty, "| pseudo:", results.stay_pseudo_evidence);
  fs.writeFileSync(path.join(EV, "delta_stay_text2.txt"), st.slice(0, 3000), "utf8");
  await shot("04_stay");
  await leakageScan(page, "stay");

  // ---- H2: bookings hostile non-JSON
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const pre = errors.length;
  const jta = page.locator("#reservation-json");
  if (await jta.isVisible().catch(() => false)) {
    await jta.fill("我的火车票 G1655 厦门北到福州南，明天上午 9 点");
    const sub = page.locator("button:has-text('保护这条预订'), button:has-text('预订')").first();
    await sub.click().catch(() => {});
    await page.waitForTimeout(4000);
    const fb = await page.locator("body").innerText().catch(() => "");
    results.h2_visible_feedback = /无效|格式|JSON|失败|无法|解析/.test(fb);
    results.h2_pageerrors = errors.length - pre;
    log("H2 visible feedback:", results.h2_visible_feedback, "| pageerrors:", results.h2_pageerrors);
  } else { results.h2_textarea_present = false; log("H2 textarea gone (redesigned?)"); }
  await shot("05_bookings_hostile");
  results.leak_bookings = await leakageScan(page, "bookings");

  // ---- positive: offline
  await ctx.setOffline(true);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(6000);
  const off = await page.locator("body").innerText().catch(() => "");
  results.offline_banner = /离线/.test(off);
  log("PC offline banner:", results.offline_banner);
  await shot("06_offline");
  await ctx.setOffline(false);

  results.pageErrors = errors.slice(0, 20);
  fs.writeFileSync(path.join(EV, "delta_verify2_summary.json"), JSON.stringify(results, null, 2), "utf8");
  await browser.close();
  log("DONE");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

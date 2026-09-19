// Copilot v3 (correct send button) + Today blank diagnosis (intercept experience API)
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const apiLog = [];
const consoleErrors = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => { consoleErrors.push({ msg: String(err).slice(0, 300) }); log("pageerror", { msg: String(err).slice(0, 150) }); });
  page.on("response", async (res) => {
    const u = res.url();
    if (u.includes("/api/") && (u.includes("experience") || u.includes("journeys"))) {
      let bodyHead = "";
      try { bodyHead = (await res.text()).slice(0, 900); } catch { bodyHead = "(body unavailable)"; }
      apiLog.push({ url: u.slice(0, 160), status: res.status(), bodyHead });
    }
  });
  const shot = async (n) => { const p = path.join(OUT, `cp_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  await shot("04_today_diag");
  log("today_body", { text: (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 500) });

  // open dock and ask
  await page.getByText("CityNexus Copilot").first().click().catch(() => {});
  await page.waitForTimeout(2000);
  const box = page.locator("textarea:visible, input[type='text']:visible").last();
  await box.fill("鼓浪屿好玩吗？适合下午去吗？");
  await shot("05_filled");
  await page.getByRole("button", { name: /询问 Copilot|Ask Copilot/ }).first().click().catch((e) => log("ask_click_fail", { err: String(e).slice(0, 150) }));
  let replySnippet = "";
  for (let i = 0; i < 18; i++) {
    await page.waitForTimeout(3000);
    const body = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
    const idx = body.indexOf("鼓浪屿好玩吗");
    if (idx >= 0) {
      const tail = body.slice(idx + 9).trim();
      if (tail.length > 30) { replySnippet = tail; break; }
    }
  }
  await shot("06_reply");
  const bodyAll = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  const terms = ["PlanVersion", "JourneyTwin", "REQUEST_PLACE_SEARCH", "UNVERIFIED", "DeepSeek", "Hermes", "C4_Anchored", "C3_Guaranteed", "tool_name", "STALE", "materialize", "What-if", "SELECT_", "agent_run"];
  const leaks = {};
  for (const t of terms) { if (bodyAll.includes(t)) leaks[t] = true; }
  const buttons = await page.locator("button:visible").allInnerTexts().catch(() => []);
  log("reply_scan", { leaks, buttons: buttons.map((b) => b.trim()).filter(Boolean).slice(0, 30), replySnippet: replySnippet.slice(0, 900), bodySample: bodyAll.slice(0, 1600) });

  fs.writeFileSync(path.join(EV, "copilot_trace_v3.json"), JSON.stringify({ trace, apiLog, consoleErrors }, null, 2), "utf8");
  await browser.close();
  log("done", { apiCalls: apiLog.length, consoleErrorCount: consoleErrors.length });
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\copilot_v3_fatal.txt", String(e), "utf8"); process.exit(1); });

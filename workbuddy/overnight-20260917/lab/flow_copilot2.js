// Copilot hostile QA v2: open dock first
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const consoleErrors = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => { consoleErrors.push({ msg: String(err).slice(0, 300) }); log("pageerror", { msg: String(err).slice(0, 200) }); });
  const shot = async (n) => { const p = path.join(OUT, `cp_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  await shot("00_today_check");
  log("today_text", { sample: (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 700) });

  // open the copilot dock
  await page.getByText("CityNexus Copilot").first().click().catch((e) => log("dock_open_fail", { err: String(e).slice(0, 150) }));
  await page.waitForTimeout(2500);
  await shot("01_dock_open");
  const inputs = page.locator("textarea:visible, input[type='text']:visible");
  log("inputs_after_open", { count: await inputs.count() });
  const bodyText0 = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  log("dock_text", { sample: bodyText0.slice(0, 1200) });

  const box = inputs.last();
  await box.fill("鼓浪屿好玩吗？适合下午去吗？");
  await shot("02_filled");
  await box.press("Enter").catch(() => {});
  await page.waitForTimeout(2000);
  const still = await box.inputValue().catch(() => "gone");
  if (still && still.length > 0) {
    await page.locator("button:visible").evaluateAll((btns) => {
      const send = btns.find((b) => /发送|Send|送出/.test(b.innerText || ""));
      if (send) send.click();
    }).catch(() => {});
    log("send_fallback", { note: "clicked send-like button" });
  }
  let replySnippet = "";
  for (let i = 0; i < 16; i++) {
    await page.waitForTimeout(3000);
    const body = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
    const idx = body.indexOf("鼓浪屿好玩吗");
    const tail = idx >= 0 ? body.slice(idx) : body;
    if (/好玩|适合|下午|鼓浪屿/.test(tail.slice(0, 800)) && tail.length > bodyText0.length + 50) { replySnippet = tail; }
    if (i >= 5 && replySnippet.length > 100) break;
  }
  await shot("03_reply");
  const bodyAll = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  const terms = ["PlanVersion", "JourneyTwin", "REQUEST_PLACE_SEARCH", "UNVERIFIED", "DeepSeek", "Hermes", "C4_Anchored", "C3_Guaranteed", "tool_name", "STALE", "materialize", "What-if"];
  const leaks = {};
  for (const t of terms) { if (bodyAll.includes(t)) leaks[t] = true; }
  const buttons = await page.locator("button:visible").allInnerTexts().catch(() => []);
  log("reply_scan", { leaks, buttons: buttons.map((b) => b.trim()).filter(Boolean).slice(0, 30), replySnippet: replySnippet.slice(0, 800), bodySample: bodyAll.slice(0, 1500) });

  fs.writeFileSync(path.join(EV, "copilot_trace.json"), JSON.stringify({ trace, consoleErrors }, null, 2), "utf8");
  await browser.close();
  log("done", { consoleErrorCount: consoleErrors.length });
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\copilot_fatal.txt", String(e), "utf8"); process.exit(1); });

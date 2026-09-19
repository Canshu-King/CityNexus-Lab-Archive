// Copilot hostile QA: consumer question -> observe reply language, action buttons, internal term leakage
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

  await page.goto("http://localhost:5181/v8/copilot", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/copilot", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await shot("00_page");
  log("page_text", { sample: (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 800) });

  // find composer input
  const inputs = page.locator("textarea:visible, input[type='text']:visible");
  const n = await inputs.count();
  log("inputs_found", { count: n });
  if (n === 0) { await shot("00_no_input"); throw new Error("no visible composer input"); }
  const box = inputs.last();
  await box.fill("鼓浪屿好玩吗？适合下午去吗？");
  await shot("01_filled");
  // try Enter then fallback to send button
  await box.press("Enter").catch(() => {});
  await page.waitForTimeout(1500);
  // detect if message sent (composer cleared) else click a send-like button
  const stillFilled = await box.inputValue().catch(() => "gone");
  if (stillFilled && stillFilled.length > 0) {
    const sent = await page.getByRole("button", { name: /发送|送出|Send/ }).first().click().then(() => "btn").catch(async () => {
      await box.press("Enter"); return "enter2";
    });
    log("send_method", { method: sent });
  }
  // poll for reply up to 45s
  let replyText = "";
  for (let i = 0; i < 15; i++) {
    await page.waitForTimeout(3000);
    const body = await page.locator("body").innerText().catch(() => "");
    const m = body.match(/鼓浪屿[\s\S]{20,600}/);
    if (m && m[0].length > 60) { replyText = m[0]; break; }
    replyText = body;
  }
  await shot("02_after_reply");
  const bodyAll = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  // scan for internal terms & action buttons
  const terms = ["PlanVersion", "JourneyTwin", "REQUEST_PLACE_SEARCH", "UNVERIFIED", "DeepSeek", "Hermes", "C4", "C3", "tool", "STALE", "materialize", "What-if"];
  const leaks = {};
  for (const t of terms) { if (bodyAll.includes(t)) leaks[t] = true; }
  const buttons = await page.locator("button:visible").allInnerTexts().catch(() => []);
  log("reply_scan", { leaks, buttons: buttons.map((b) => b.trim()).filter(Boolean).slice(0, 25), replySnippet: replyText.replace(/\s+/g, " ").slice(0, 600) });

  // second question: replan intent
  const box2 = page.locator("textarea:visible, input[type='text']:visible").last();
  await box2.fill("下暴雨了，帮我调整明天的安排").catch(() => {});
  await box2.press("Enter").catch(() => {});
  await page.waitForTimeout(1000);
  const sf2 = await box2.inputValue().catch(() => "gone");
  if (sf2 && sf2.length > 0) await page.getByRole("button", { name: /发送|Send/ }).first().click().catch(() => {});
  await page.waitForTimeout(20000);
  await shot("03_after_replan_q");
  const bodyAll2 = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  const leaks2 = {};
  for (const t of terms) { if (bodyAll2.includes(t)) leaks2[t] = true; }
  log("replan_scan", { leaks: leaks2, snippet: bodyAll2.slice(0, 900) });

  fs.writeFileSync(path.join(EV, "copilot_trace.json"), JSON.stringify({ trace, consoleErrors }, null, 2), "utf8");
  await browser.close();
  log("done", { consoleErrorCount: consoleErrors.length });
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\copilot_fatal.txt", String(e), "utf8"); process.exit(1); });

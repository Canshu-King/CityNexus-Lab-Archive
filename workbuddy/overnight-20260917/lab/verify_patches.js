// Verify shadow patches P1/P2/P3 in isolated snapshot (vite 5181)
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const shot = async (n) => { const p = path.join(OUT, `pt_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  // ---------- P1a: non-JSON -> friendly error ----------
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const ta = page.locator("#reservation-json");
  await ta.fill("我的高铁票是明天早上9点30分从厦门北到福州南");
  await page.getByRole("button", { name: /审核并保护/ }).click();
  await page.waitForTimeout(1500);
  await shot("00_nonjson_error");
  const errText = await page.locator('[role="alert"]').innerText().catch(() => "(no alert)");
  log("P1a_nonjson_error", { alert: errText.replace(/\s+/g, " ") });

  // ---------- P1b: valid JSON with nested price -> card shows route + friendly labels ----------
  await ta.fill(JSON.stringify({
    reservation_type: "RAIL",
    confirmation_ref: "WB-PATCH-TEST-001",
    origin: "厦门北",
    destination: "福州南",
    scheduled_departure_at: "2026-09-21T09:30:00+08:00",
    scheduled_arrival_at: "2026-09-21T10:42:00+08:00",
    price: { amount_minor: 12800, currency: "CNY" },
  }));
  await page.getByRole("button", { name: /审核并保护/ }).click();
  await page.waitForTimeout(4000);
  await shot("01_valid_after_patch");
  const cardText = (await page.locator('[data-testid="wallet-reservation"]').last().innerText().catch(() => "(no card)")).replace(/\s+/g, " ");
  log("P1b_card", { cardText: cardText.slice(0, 250) });

  // ---------- P3: Copilot consumer language ----------
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  await page.getByText("CityNexus Copilot").first().click();
  await page.waitForTimeout(2000);
  await shot("02_dock_patched");
  const dockHead = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  log("P3_dock_head", { hasDeepSeek: dockHead.includes("DeepSeek"), hasHermes: dockHead.includes("Hermes"), hasSemanticBar: dockHead.includes("Semantic:") });
  const box = page.locator("textarea:visible, input[type='text']:visible").last();
  await box.fill("鼓浪屿好玩吗？适合下午去吗？");
  await page.getByRole("button", { name: /询问 Copilot|Ask Copilot/ }).first().click();
  await page.waitForTimeout(15000);
  await shot("03_reply_patched");
  const dockAfter = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  const leaks = {};
  for (const t of ["REQUEST_PLACE_SEARCH", "DISCOVER", "DeepSeek", "Hermes", "UNVERIFIED"]) { if (dockAfter.includes(t)) leaks[t] = true; }
  log("P3_reply_scan", { leaks, hasFriendlySearch: dockAfter.includes("搜索候选地点"), hasExploreChip: dockAfter.includes("探索"), snippet: dockAfter.slice(0, 700) });

  // ---------- P2: AI plan honest terminal state ----------
  await page.goto("http://localhost:5181/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const aiBtn = page.getByRole("button", { name: /AI 帮我规划/ }).first();
  if (await aiBtn.isVisible().catch(() => false)) {
    await aiBtn.click();
    await page.waitForTimeout(1500);
    const sheet = page.locator('[data-testid="plan-ai-sheet"]');
    const ta2 = sheet.locator("textarea").first();
    await ta2.fill("我和朋友两个人去厦门，想轻松一点，想去鼓浪屿、环岛路，想吃沙茶面和海鲜，不想太赶。");
    await shot("04_ai_filled");
    const goBtn = sheet.locator("button").last();
    await goBtn.click().catch((e) => log("ai_click_fail", { err: String(e).slice(0, 120) }));
    await page.waitForTimeout(25000);
    await shot("05_ai_terminal");
    const sheetText = (await sheet.innerText().catch(() => "(sheet gone)")).replace(/\s+/g, " ");
    log("P2_terminal", { text: sheetText.slice(0, 400), honestReady: sheetText.includes("这次没能生成方案"), fakeReady: sheetText.includes("方案已准备好") });
  } else {
    log("P2_skipped", { reason: "AI button not visible on trips" });
  }

  fs.writeFileSync(path.join(EV, "patch_verify_trace.json"), JSON.stringify(trace, null, 2), "utf8");
  await browser.close();
  log("done", {});
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\patch_verify_fatal.txt", String(e), "utf8"); process.exit(1); });

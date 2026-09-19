// Hostile bookings import flow: valid JSON / missing fields / non-JSON text
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
  page.on("pageerror", (err) => { consoleErrors.push({ kind: "pageerror", msg: String(err).slice(0, 500) }); log("pageerror", { msg: String(err).slice(0, 300) }); });
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push({ kind: "console", msg: m.text().slice(0, 500) }); });
  const shot = async (n) => { const p = path.join(OUT, `bk_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };
  const bodyText = async () => (await page.locator("body").innerText().catch(() => "")).replace(/\n+/g, " | ");

  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await shot("00_page");
  log("bookings_page_text", { sample: (await bodyText()).slice(0, 900) });

  const ta = page.locator("#reservation-json");
  const btn = page.getByRole("button", { name: /审核并保护|Review and protect/i });

  // ---------- Case A: complete valid RAIL JSON ----------
  const valid = JSON.stringify({
    reservation_type: "RAIL",
    confirmation_ref: "WB-RAIL-20260918-001",
    origin: "厦门北",
    destination: "福州南",
    scheduled_departure_at: "2026-09-18T09:30:00+08:00",
    scheduled_arrival_at: "2026-09-18T10:42:00+08:00",
    provider: "中国铁路 12306",
    price: { amount_minor: 12800, currency: "CNY" },
  });
  await ta.fill(valid);
  await shot("01_valid_filled");
  const btnAEnabled = await btn.isEnabled().catch(() => false);
  await btn.click().catch((e) => log("caseA_click_fail", { err: String(e).slice(0, 200) }));
  await page.waitForTimeout(3500);
  await shot("02_valid_after_submit");
  log("caseA", { btnEnabledBefore: btnAEnabled, text: (await bodyText()).slice(0, 1200) });
  const reservationsA = await page.locator('[data-testid="wallet-reservation"]').count();
  log("caseA_wallet_cards", { count: reservationsA });

  // ---------- Case B: missing critical fields ----------
  await ta.fill('{"reservation_type":"HOTEL"}');
  await btn.click().catch((e) => log("caseB_click_fail", { err: String(e).slice(0, 200) }));
  await page.waitForTimeout(3000);
  await shot("03_missing_fields_after");
  log("caseB", { text: (await bodyText()).slice(0, 1200) });

  // ---------- Case C: non-JSON natural language ----------
  await ta.fill("我的高铁票是明天早上9点30分从厦门北到福州南，车次G1655，座位二等座12车8A");
  const btnCEnabled = await btn.isEnabled().catch(() => false);
  await btn.click().catch((e) => log("caseC_click_fail", { err: String(e).slice(0, 200) }));
  await page.waitForTimeout(2500);
  await shot("04_nonjson_after");
  log("caseC", { btnEnabledBefore: btnCEnabled, text: (await bodyText()).slice(0, 1200) });
  // does UI show any feedback? (we expect none -> silent unhandled rejection)
  const toastVisible = await page.locator("text=/失败|错误|无效|格式/").first().isVisible().catch(() => false);
  log("caseC_feedback_visible", { errorFeedback: toastVisible });

  // ---------- Case D: double-click protection ----------
  await ta.fill('{"reservation_type":"RAIL","confirmation_ref":"WB-DOUBLE-CLICK-TEST","origin":"厦门北","destination":"福州南","scheduled_departure_at":"2026-09-19T09:30:00+08:00","scheduled_arrival_at":"2026-09-19T10:42:00+08:00"}');
  const [r1, r2] = await Promise.all([
    btn.click().then(() => "ok").catch(() => "fail"),
    btn.click().then(() => "ok").catch(() => "fail"),
  ]).catch(() => ["err", "err"]);
  await page.waitForTimeout(3500);
  await shot("05_doubleclick_after");
  const dblCards = await page.locator('[data-testid="wallet-reservation"]').count();
  const dblRefs = await page.locator('[data-testid="wallet-reservation"]').allInnerTexts().catch(() => []);
  log("caseD_double_click", { clicks: [r1, r2], totalCards: dblCards, refs: dblRefs.map((t) => t.replace(/\s+/g, " ").slice(0, 80)) });

  fs.writeFileSync(path.join(EV, "bookings_hostile_trace.json"), JSON.stringify({ trace, consoleErrors }, null, 2), "utf8");
  await browser.close();
  log("done", { consoleErrorCount: consoleErrors.length });
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\bookings_hostile_fatal.txt", String(e), "utf8"); process.exit(1); });

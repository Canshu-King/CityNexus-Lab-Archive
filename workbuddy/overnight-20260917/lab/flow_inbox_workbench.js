// Multimodal inbox workbench: text-extract path + manual form path
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
  page.on("pageerror", (err) => { consoleErrors.push({ kind: "pageerror", msg: String(err).slice(0, 400) }); log("pageerror", { msg: String(err).slice(0, 200) }); });
  const shot = async (n) => { const p = path.join(OUT, `ibx_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };
  const msg = async () => (await page.locator(".v10-inbox-message").innerText().catch(() => "(no message)")).replace(/\s+/g, " ");

  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);

  // scroll workbench into view
  await page.locator('[aria-label="行程收件箱提取"], [aria-label="Journey inbox extraction"]').first().scrollIntoViewIfNeeded().catch(() => log("scroll_fail", {}));
  await page.waitForTimeout(800);
  await shot("00_workbench");

  // ---- Path 1: paste natural-language confirmation text ----
  const ta = page.locator(".v10-inbox-inputs textarea").first();
  await ta.fill("您好，您已成功购买 2026年9月20日 G1687 次列车，厦门北 08:15 开，福州南 09:32 到，二等座 12车05A号，票价 129.5 元，订单号 E2938475812。【中国铁路12306】");
  await page.getByRole("button", { name: /提取文本草稿|Extract text draft/ }).click().catch((e) => log("extractText_click_fail", { err: String(e).slice(0, 150) }));
  await page.waitForTimeout(8000);
  await shot("01_text_extract_result");
  log("text_extract_message", { message: await msg() });

  // ---- Path 2: manual form ----
  await page.locator('[data-testid="inbox-tab-manual"]').click();
  await page.waitForTimeout(600);
  await shot("02_manual_form");
  await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
  await page.locator('[data-testid="manual-title"]').fill("G1687 厦门北→福州南");
  await page.locator('[data-testid="manual-ref"]').fill("E2938475812");
  await page.locator('[data-testid="manual-amount"]').fill("129.5");
  await shot("03_manual_filled");
  await page.locator('[data-testid="manual-submit"]').click().catch((e) => log("manual_click_fail", { err: String(e).slice(0, 150) }));
  await page.waitForTimeout(3500);
  await shot("04_manual_after");
  log("manual_message", { message: await msg() });

  // full page long screenshot for the report
  await page.screenshot({ path: path.join(OUT, "ibx_05_fullpage.png"), fullPage: true });
  log("done", { consoleErrorCount: consoleErrors.length });
  fs.writeFileSync(path.join(EV, "inbox_workbench_trace.json"), JSON.stringify({ trace, consoleErrors }, null, 2), "utf8");
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\inbox_workbench_fatal.txt", String(e), "utf8"); process.exit(1); });

// Domain D: hotel stay-options flow via menu -> 住宿选择
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
    if (u.includes("/api/") && (u.includes("stay") || u.includes("option") || u.includes("hotel"))) {
      let bodyHead = "";
      try { bodyHead = (await res.text()).slice(0, 700); } catch { bodyHead = "(na)"; }
      apiLog.push({ url: u.slice(0, 150), status: res.status(), bodyHead });
    }
  });
  const shot = async (n) => { const p = path.join(OUT, `ht_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  // open menu
  await page.getByText("菜单").first().click().catch((e) => log("menu_fail", { err: String(e).slice(0, 120) }));
  await page.waitForTimeout(1500);
  // click 住宿选择
  await page.getByText("住宿选择").first().click().catch((e) => log("stay_link_fail", { err: String(e).slice(0, 120) }));
  await page.waitForTimeout(6000);
  await shot("00_stay_page");
  const body0 = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
  log("stay_page_text", { text: body0.slice(0, 1300) });

  // look for hotel option cards / select buttons
  const selBtns = page.getByRole("button", { name: /选择|选定|查看|确认/ }).first();
  const hasSel = await selBtns.isVisible().catch(() => false);
  log("select_btn_visible", { hasSel });
  if (hasSel) {
    await selBtns.click().catch((e) => log("sel_click_fail", { err: String(e).slice(0, 150) }));
    await page.waitForTimeout(5000);
    await shot("01_after_select");
    log("after_select_text", { text: (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 900) });
  }
  await page.screenshot({ path: path.join(OUT, "ht_02_fullpage.png"), fullPage: true });
  fs.writeFileSync(path.join(EV, "hotel_flow_trace.json"), JSON.stringify({ trace, apiLog, consoleErrors }, null, 2), "utf8");
  await browser.close();
  log("done", { apiCalls: apiLog.length });
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\hotel_flow_fatal.txt", String(e), "utf8"); process.exit(1); });

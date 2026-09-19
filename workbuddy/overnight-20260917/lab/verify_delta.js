// Delta verification for WB-H2/H3/H4/H5 + positive controls (snapshot_0957 stack)
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `dlt_${n}.png`) }); log("shot", n); };
  const leakageScan = async (label) => {
    const text = await page.locator("body").innerText().catch(() => "");
    const bad = ["DeepSeek", "Hermes", "Semantic:", "REQUEST_PLACE_SEARCH", "PlanVersion", "JourneyTwin", "受保护 C4", "UNKNOWN_REALTIME", "UNVERIFIED", "DISCOVER"];
    const hits = bad.filter((b) => text.includes(b));
    log(`LEAK[${label}]:`, hits.length ? hits.join(", ") : "clean");
    return { label, hits };
  };

  // ---- H4: Today empty state (fresh context, no journey)
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const todayText = await page.locator("body").innerText().catch(() => "");
  fs.writeFileSync(path.join(EV, "delta_today_notext.txt"), todayText.slice(0, 3000), "utf8");
  log("H4 today body chars:", todayText.length);
  log("H4 today has CTA(规划/开始/创建):", /规划|开始|创建|设置/.test(todayText));
  await shot("01_today");

  // ---- H4b: Copilot route
  await page.goto("http://localhost:5181/v8/copilot", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const copText = await page.locator("body").innerText().catch(() => "");
  log("H4b copilot route chars:", copText.length);
  await shot("02_copilot_route");

  // ---- H3: Copilot dialog with journey set
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const dockBar = page.locator("text=/Copilot|助手|问/i").first();
  if (await dockBar.isVisible().catch(() => false)) { await dockBar.click().catch(() => {}); await page.waitForTimeout(1500); }
  const sendBtn = page.getByRole("button", { name: /询问 Copilot|发送|提问/ }).first();
  if (await sendBtn.isVisible().catch(() => false)) log("send button found");
  const ta = page.locator("textarea").last();
  await ta.fill("鼓浪屿好玩吗？帮我看看");
  await sendBtn.click().catch(async () => { await ta.press("Enter"); });
  log("question sent, waiting reply...");
  let replySeen = false;
  const t0 = Date.now();
  while (Date.now() - t0 < 90000) {
    await page.waitForTimeout(8000);
    const bubbles = await page.locator("article").count().catch(() => 0);
    if (bubbles >= 2) { replySeen = true; break; }
  }
  log("reply visible:", replySeen, `after ${Math.round((Date.now() - t0) / 1000)}s`);
  await page.waitForTimeout(2000);
  const leakCopilot = await leakageScan("copilot");
  await shot("03_copilot_reply");

  // ---- H5: StayExplorer via menu
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const burger = page.locator("[aria-label*=菜单], button:has-text('☰')").first();
  if (await burger.isVisible().catch(() => false)) { await burger.click(); await page.waitForTimeout(1000); }
  const stayLink = page.locator("text=/住宿|酒店/").first();
  if (await stayLink.isVisible().catch(() => false)) { await stayLink.click(); await page.waitForTimeout(6000); }
  await leakageScan("stay");
  const stayText = await page.locator("body").innerText().catch(() => "");
  log("H5 stay has honest empty:", /还没有可用的住宿候选|暂无供应商证据/.test(stayText));
  log("H5 stay has pseudo evidence:", /0% confidence|Provider price unavailable/.test(stayText));
  fs.writeFileSync(path.join(EV, "delta_stay_text.txt"), stayText.slice(0, 3000), "utf8");
  await shot("04_stay");

  // ---- H2: bookings JSON hostile (non-JSON text)
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const pre = errors.slice();
  const jta = page.locator("#reservation-json");
  if (await jta.isVisible().catch(() => false)) {
    await jta.fill("我的火车票 G1655 厦门北到福州南，明天上午 9 点");
    const sub = page.locator("button:has-text('保护这条预订'), button:has-text('预订')").first();
    await sub.click().catch(() => {});
    await page.waitForTimeout(4000);
    const feedback = await page.locator("body").innerText().catch(() => "");
    log("H2 non-JSON visible feedback:", /无效|格式|JSON|失败|无法/.test(feedback));
    log("H2 pageerror count during submit:", errors.length - pre.length);
  } else {
    log("H2 reservation-json textarea NOT visible (may have been redesigned)");
  }
  await shot("05_bookings_hostile");
  await leakageScan("bookings");

  // ---- positive control: offline read-only on Today
  await ctx.setOffline(true);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(6000);
  const offText = await page.locator("body").innerText().catch(() => "");
  log("PC offline banner:", /离线/.test(offText), "| chars:", offText.length);
  await shot("06_offline");
  await ctx.setOffline(false);

  fs.writeFileSync(path.join(EV, "delta_verify_summary.json"), JSON.stringify({ when: new Date().toISOString(), leakCopilot, pageErrors: errors.slice(0, 20) }, null, 2), "utf8");
  await browser.close();
  log("DONE");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

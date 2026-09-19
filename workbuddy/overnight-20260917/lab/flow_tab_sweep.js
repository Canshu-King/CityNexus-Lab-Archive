// Tab sweep: trips / map / me / menu -> screenshots + leak scan
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const trace = [];
const log = (s, d) => { const e = { ts: new Date().toISOString(), step: s, ...d }; trace.push(e); console.log(JSON.stringify(e)); };
const TERMS = ["PlanVersion", "JourneyTwin", "REQUEST_PLACE_SEARCH", "UNVERIFIED", "DeepSeek", "Hermes", "C4_Anchored", "C3_Guaranteed", "tool_name", "STALE_", "materialize", "What-if", "SELECT_", "UNKNOWN_REALTIME", "MATERIAL", "PROVIDER", "anchor", "semantic"];
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const shot = async (n) => { const p = path.join(OUT, `tab_${n}.png`); await page.screenshot({ path: p }); log("shot", { n, file: p }); };

  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  const visit = async (route, name) => {
    await page.goto(`http://localhost:5181/v8/${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5500);
    await shot(name);
    const text = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
    const leaks = {};
    for (const t of TERMS) { if (text.includes(t)) leaks[t] = text.indexOf(t) >= 0 ? text.slice(Math.max(0, text.indexOf(t) - 40), text.indexOf(t) + 60) : true; }
    log(`tab_${name}`, { textSample: text.slice(0, 700), leaks });
    return text;
  };

  const trips = await visit("trips", "trips");
  // if trips has plan/hotel content, try clicking hotel-related entries
  const hotelLink = page.getByText(/酒店|住宿|stay/i).first();
  if (await hotelLink.isVisible().catch(() => false)) {
    await hotelLink.click().catch(() => {});
    await page.waitForTimeout(4000);
    await shot("trips_hotel");
    const t2 = (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ");
    const leaks2 = {};
    for (const t of TERMS) { if (t2.includes(t)) leaks2[t] = true; }
    log("trips_hotel_detail", { textSample: t2.slice(0, 700), leaks: leaks2 });
  }
  await visit("map", "map");
  await visit("me", "me");
  // hamburger menu
  await page.getByText("菜单").first().click().catch(() => {});
  await page.waitForTimeout(2000);
  await shot("menu_open");
  log("menu_text", { text: (await page.locator("body").innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 900) });

  fs.writeFileSync(path.join(EV, "tab_sweep_trace.json"), JSON.stringify(trace, null, 2), "utf8");
  await browser.close();
  log("done", {});
})().catch((e) => { console.error("FATAL", e.message); fs.writeFileSync("D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\tab_sweep_fatal.txt", String(e), "utf8"); process.exit(1); });

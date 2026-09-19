// Mobile UI gate recheck (R2/R3/R5/R6) — 390x844 viewport, hotfix runtime
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "screenshots");
const EV = path.join(ROOT, "evidence");
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const EXE = "C:\\Users\\仓鼠王\\AppData\\Local\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";

const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (n, o) => fs.writeFileSync(path.join(EV, n), JSON.stringify(o, null, 2), "utf8");

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const shot = async (n) => { const p = path.join(OUT, `rc2_${n}.png`); await page.screenshot({ path: p }); log("shot", n); };
  const text = () => page.locator("body").innerText().catch(() => "");

  // R5 + R6: Trips page — dock overlap + raw role keys
  await page.goto(`http://[::1]:5181/v8/trips?journey=${JID}`, { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2500);
  await shot("01_trips");
  const tripsText = await text();
  save("rc2_trips_text.json", { length: tripsText.length, text: tripsText.slice(0, 3000) });
  const r5hits = ["check_out", "departure", "museum"].filter((k) => tripsText.includes(k));
  log("R5 raw keys visible:", r5hits.length ? r5hits.join(",") : "none");

  // R3: Bookings — default path internal vocabulary
  await page.goto(`http://[::1]:5181/v8/bookings?journey=${JID}`, { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2500);
  await shot("02_bookings");
  const bkText = await text();
  save("rc2_bookings_text.json", { length: bkText.length, text: bkText.slice(0, 3000) });
  const r3hits = ["UNKNOWN", "STRUCTURED_JSON", "DETERMINISTIC", "manual-entry", "Journey Memory", "受保护 C4", "UNKNOWN_REALTIME", "anchor", "Departure"].filter((k) => bkText.includes(k));
  log("R3 internal vocab visible:", r3hits.length ? r3hits.join(" | ") : "none");

  // R2/R6: Live — pending proposal cards + dock obstruction
  await page.goto(`http://[::1]:5181/v8/live?journey=${JID}`, { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2500);
  await shot("03_live");
  const liveText = await text();
  save("rc2_live_text.json", { length: liveText.length, text: liveText.slice(0, 3000) });
  const acceptBtns = await page.locator("button", { hasText: "接受新方案" }).count().catch(() => -1);
  const cards = await page.locator("text=移除 1 项 · 新增 1 项").count().catch(() => -1);
  log("R2 accept buttons:", acceptBtns, "identical summaries:", cards);

  // R6: dock vs sheet — open AI planning sheet from Today, check overlap
  await page.goto(`http://[::1]:5181/v8/today?journey=${JID}`, { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await shot("04_today");

  await browser.close();
  log("done");
})().catch((e) => { console.error("FATAL", e); process.exit(1); });

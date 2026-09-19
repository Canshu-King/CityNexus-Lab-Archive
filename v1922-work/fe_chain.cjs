const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rc_evidence/shots";
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/rc_evidence/be_chain.json", "utf8"));
const JID = chain.journey_id;
fs.mkdirSync(SHOTS, { recursive: true });
const TRACE = [];
const rec = (route, action, status, result) =>
  TRACE.push({ ts: new Date().toISOString(), route, action, status, result: String(result).slice(0, 160) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN",
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C:" + m.text().slice(0, 160)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  // 行程
  await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const trips = await page.locator("body").innerText();
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  rec("/v8/trips", "itinerary", "200", `stops=${stops}`);
  // 是否出现厦门 POI 名（真实 OSM 名称）
  const xiamen = /星巴克|图书馆|OSM cafe|OSM restaurant|厦门/.test(trips);
  rec("/v8/trips", "xiamen-places-visible", xiamen ? "YES" : "NO", trips.replace(/\n+/g, " | ").slice(0, 140));
  await page.screenshot({ path: SHOTS + "/X1_itinerary.png", fullPage: true });

  // 地图
  await page.goto(BASE + "/v8/map", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);
  const mapTxt = await page.locator("body").innerText();
  const hasMap = await page.locator('[data-testid="v8-maplibre-panel"]').count() > 0;
  const emptyState = await page.locator('[data-testid="v8-map-empty"]').count() > 0;
  rec("/v8/map", "map", hasMap ? "map-rendered" : "empty-state", mapTxt.replace(/\n+/g, " | ").slice(0, 140));
  await page.screenshot({ path: SHOTS + "/X2_map.png", fullPage: true });

  // 今天：方案比较
  await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);
  const cmp = await page.locator('[data-testid="plan-cmp-card"]').count();
  rec("/v8/hub", "plan-comparison", `cards=${cmp}`, "");
  await page.screenshot({ path: SHOTS + "/X3_today.png", fullPage: true });

  // Copilot 厦门问题（真实 DeepSeek）
  await page.goto(BASE + "/v8/agent", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  await page.locator('[data-testid="v15-copilot-input"]').fill("鼓浪屿好玩吗？");
  await page.locator('[data-testid="v15-copilot-submit"]').click();
  await page.waitForTimeout(12000);
  const agent = await page.locator("body").innerText();
  const leaks = /REQUEST_PLACE_SEARCH|REQUEST_REPLAN|ACCEPT_REPLAN|PlanVersion|semantic_key|C4_Anchored/.test(agent);
  rec("/v8/agent", "copilot-xiamen", leaks ? "enum-leak" : "clean", agent.replace(/\n+/g, " | ").slice(-220));
  await page.screenshot({ path: SHOTS + "/X4_copilot.png", fullPage: true });

  fs.writeFileSync("D:/moodle/_v1922_work/rc_evidence/fe_trace.json",
    JSON.stringify({ journey_id: JID, trace: TRACE, errors: errors.slice(0, 8) }, null, 1));
  TRACE.forEach((t) => console.log(`${t.route.padEnd(12)} ${t.action.padEnd(24)} ${String(t.status).padEnd(14)} ${t.result.slice(0, 90)}`));
  console.log("ERRORS:", errors.length);
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

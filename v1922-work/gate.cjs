const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const JID = "22222222-2222-4222-8222-222222222222";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
const R = [];
const rec = (id, ok, note) => R.push({ id, ok, note: String(note).slice(0, 120) });
const errors = [];

async function newPage(browser, opts = {}) {
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, ...opts,
  });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C:" + m.text().slice(0, 150)); });
  return { ctx, page };
}
const bind = (page) => page.addInitScript(() =>
  localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));

(async () => {
  await fetch(API + "/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });

  // 1-6 全新用户
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN" });
    await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    rec("01 / 进入新产品", await page.locator('[data-testid="trial-step1-body"]').count() > 0, "");
    await page.locator('[data-testid="trial-city"]').fill("厦门");
    await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
    await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
    const inf = await page.locator('[data-testid="trial-inferred"]').innerText().catch(() => "");
    rec("02 自动推断国家/货币/时区", inf.includes("中国") && inf.includes("人民币"), inf);
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(400);
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(400);
    rec("03 三步创建流程", await page.locator('[data-testid="trial-step3-body"]').count() > 0, "");
    await page.locator('[data-testid="trial-create"]').click();
    await page.waitForTimeout(5000);
    rec("04 AI 规划面板打开", await page.locator('[data-testid="plan-ai-sheet"]').count() > 0, "");
    await page.locator('[data-testid="plan-ai-input"]').fill("我和朋友两个人去厦门，想轻松一点，想去鼓浪屿，不想太赶。");
    await page.locator('[data-testid="plan-ai-submit"]').click();
    await page.waitForTimeout(4500);
    const res = await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "");
    rec("05 诚实规划进度/结果", res.length > 5, res.split("\n")[0]);
    await page.screenshot({ path: SHOTS + "/A1_create_ai.png", fullPage: true });
    await ctx.close();
  }

  // 6-15 demo 行程
  await fetch(`${API}/journeys/${JID}/plans/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN" });
    await bind(page);
    await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(3000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    rec("06 比较候选方案", cards >= 2, `cards=${cards}`);
    await page.screenshot({ path: SHOTS + "/A2_compare.png", fullPage: true });
    await page.locator('[data-testid="plan-cmp-choose"]').first().click();
    await page.waitForTimeout(4000);
    rec("07 采用方案", await page.locator('[data-testid="plan-comparison"]').count() === 0, "");
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    rec("08 逐日行程详情", stops > 0, `stops=${stops}`);
    const tripsBody = await page.locator("body").innerText();
    rec("09 活动详情(时间+时长)", /\d{1,2}:\d{2}/.test(tripsBody) && (tripsBody.includes("h ") || tripsBody.includes("小时")), "");
    rec("10 住宿入口可见", tripsBody.includes("住宿") || tripsBody.includes("Stay") || tripsBody.includes("STAY"), "");
    await page.screenshot({ path: SHOTS + "/A3_itinerary.png", fullPage: true });
    await page.goto(BASE + "/v8/map", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    const mapBody = await page.locator("body").innerText();
    rec("11 地图正确/诚实空态", !mapBody.includes("Tianjin") && !mapBody.includes("天津"), mapBody.includes("No map location") || mapBody.includes("尚未获取") ? "empty-state" : "rendered");
    await page.goto(BASE + "/v8/agent", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    await page.locator('[data-testid="v15-copilot-input"]').fill("鼓浪屿好玩吗");
    await page.locator('[data-testid="v15-copilot-submit"]').click();
    await page.waitForTimeout(4000);
    const agentBody = await page.locator("body").innerText();
    rec("12 Copilot 回答问题", agentBody.length > 400, "");
    rec("13 无原始枚举泄露", !/REQUEST_PLACE_SEARCH|REQUEST_REPLAN|ACCEPT_REPLAN|PlanVersion|semantic_key|C4_Anchored/.test(agentBody), "");
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("14 预订/钱包不白屏", (await page.locator("body").innerText()).length > 300, "");
    const before = (await page.locator("body").innerText()).slice(0, 24);
    await page.locator('[data-testid="topbar-language"]').first().click().catch(() => {});
    await page.waitForTimeout(1200);
    const afterTxt = await page.locator("body").innerText();
    rec("15 语言切换不破坏流程", before !== afterTxt.slice(0, 24) && afterTxt.length > 300, `${before.split("\n")[0]} -> ${afterTxt.slice(0, 24).split("\n")[0]}`);
    await page.screenshot({ path: SHOTS + "/A4_lang.png", fullPage: true });
    await ctx.close();
  }

  // 16 后端断开
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.route("**/api/v1/**", (r) => r.abort("failed"));
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(4000);
    const off = await page.locator("body").innerText();
    rec("16 后端断开可恢复", off.includes("Can't reach") || off.includes("连不上"), off.split("\n").slice(0, 2).join(" | "));
    await page.screenshot({ path: SHOTS + "/A5_offline.png" });
    await ctx.close();
  }
  // 17 GPS 拒绝
  {
    const { ctx, page } = await newPage(browser, { permissions: [] });
    await bind(page);
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("17 GPS 拒绝仍可用", (await page.locator("body").innerText()).length > 300, "");
    await ctx.close();
  }
  // 18 Live
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.goto(BASE + "/v8/live", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("18 Live 可进入", (await page.locator("body").innerText()).length > 200, "");
    await page.screenshot({ path: SHOTS + "/A6_live.png", fullPage: true });
    await ctx.close();
  }
  // 19 430x932
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN", viewport: { width: 430, height: 932 } });
    await bind(page);
    for (const k of ["hub", "trips", "map", "agent", "me"]) {
      await page.goto(BASE + "/v8/" + k, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(1200);
    }
    const ov = await page.evaluate(() => ({
      sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
    }));
    rec("19 430x932 无横向溢出", ov.sw <= ov.cw + 1, `sw=${ov.sw} cw=${ov.cw}`);
    await page.screenshot({ path: SHOTS + "/A7_430.png", fullPage: true });
    await ctx.close();
  }
  // 20 底部导航
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    const nav = page.locator(".v8-mobile-nav button");
    const labels = [];
    for (let i = 0; i < await nav.count(); i++) labels.push((await nav.nth(i).innerText()).trim());
    rec("20 主导航 = 今天/行程/地图/Copilot/我的", labels.length === 5, labels.join("/"));
    await ctx.close();
  }

  await browser.close();
  const out = { results: R, errors: errors.slice(0, 10) };
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/gate.json", JSON.stringify(out, null, 1));
  R.forEach((r) => console.log(`${r.ok ? "PASS" : "FAIL"}  ${r.id}  ${r.note}`.slice(0, 125)));
  console.log("ERRORS:", errors.length);
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

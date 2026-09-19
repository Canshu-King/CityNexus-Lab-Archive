// FINAL DELTA live test B: F3 me(journey), F5 bookings(journey), F7 compare, F10 old-plan false success, F8 budget advisory
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots\\final";
const EV = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence";
fs.mkdirSync(OUT, { recursive: true });
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (p, t) => fs.writeFileSync(path.join(EV, p), t, "utf8");
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message.slice(0, 120)));
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `fb_${n}.png`) }); log("shot", n); };
  const R = {};

  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);

  // ---- F3: Me with journey
  await page.goto("http://localhost:5181/v8/me", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const meT = await page.locator("body").innerText().catch(() => "");
  R.f3 = { advisory: meT.includes("ADVISORY"), cnxiamen: meT.includes("CN-XIAMEN"), boundary: meT.includes("权限边界"), chars: meT.length };
  save("final_me_journey_text.txt", meT.slice(0, 4000));
  log("F3 me:", JSON.stringify(R.f3));
  await shot("f3_me_journey");

  // ---- F5: bookings with journey
  await page.goto("http://localhost:5181/v8/bookings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const bkT = await page.locator("body").innerText().catch(() => "");
  const BAD4 = ["STRUCTURED_JSON", "DETERMINISTIC", "Journey Memory", "DEPARTURE", "UNKNOWN", "manual-entry", "受保护 C4", "UNKNOWN_REALTIME", "DeepSeek"];
  R.f5 = { hits: BAD4.filter((b) => bkT.includes(b)), jsonTextarea: await page.locator("#reservation-json").isVisible().catch(() => false), advanced: /高级|开发者/.test(bkT), chars: bkT.length };
  save("final_bookings_journey_text.txt", bkT.slice(0, 4500));
  log("F5:", JSON.stringify(R.f5));
  const pre = errors.length;
  if (R.f5.jsonTextarea) {
    await page.locator("#reservation-json").fill("我的火车票 G1655 厦门北到福州南，明天上午 9 点发车");
    const sub = page.locator("aside button, .v9-inbox button").filter({ hasText: /保护|审核|导入/ }).first();
    await sub.click().catch(() => {});
    await page.waitForTimeout(3500);
    const after = await page.locator("body").innerText().catch(() => "");
    R.f5.feedback = /无效|格式|无法|解析|失败|请输入|合法/.test(after);
    R.f5.pageerrors = errors.length - pre;
  }
  await shot("f5_bookings_journey");

  // ---- F10: seed old plans via API, then new AI run via UI
  const plans = await page.evaluate(async (id) => {
    const g = async (u, o) => (await fetch(u, o)).json();
    const places = await g(`/api/v1/places?city_code=XIAMEN`).catch(() => []);
    const ids = (Array.isArray(places) ? places : []).map((x) => x.id).filter(Boolean).slice(0, 8);
    let seeded = null;
    if (ids.length >= 2) seeded = await g(`/api/v1/journeys/${id}/plans/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ place_ids: ids, candidate_count: 3 }) }).catch((e) => ({ err: String(e) }));
    const after = await g(`/api/v1/journeys/${id}/plans`).catch(() => []);
    return { places: (Array.isArray(places) ? places.length : 0), seededIsArray: Array.isArray(seeded) ? seeded.length : seeded, planCountAfterSeed: Array.isArray(after) ? after.length : after };
  }, JID).catch((e) => ({ err: String(e) }));
  R.f10_seed = plans;
  log("F10 seed:", JSON.stringify(plans));
  const before = plans.planCountAfterSeed;

  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const hubT = await page.locator("body").innerText().catch(() => "");
  R.f7_hub_text = hubT.slice(0, 3500);
  R.f7_budget_labels = ["预算内", "接近预算", "超预算", "花费未知", "总价未知"].filter((x) => hubT.includes(x));
  log("F7 hub labels:", R.f7_budget_labels.join(",") || "none");
  save("final_hub_text.txt", hubT.slice(0, 4500));
  await shot("f7_hub");

  const aiBtn = page.getByRole("button", { name: /AI 帮我规划|AI 规划|重新规划/ }).first();
  if (await aiBtn.isVisible().catch(() => false)) {
    await aiBtn.click();
    await page.waitForTimeout(1500);
    const inp = page.locator("[data-testid=plan-ai-input]");
    if (await inp.isVisible().catch(() => false)) {
      await inp.fill("重跑一次规划，看看这次能不能出新的候选方案");
      await page.locator("[data-testid=plan-ai-submit]").click();
      const t0 = Date.now();
      while (Date.now() - t0 < 150000) {
        await page.waitForTimeout(10000);
        const res = page.locator("[data-testid=plan-ai-result]");
        if (await res.isVisible().catch(() => false)) {
          R.f10_terminal = (await res.innerText()).replace(/\n+/g, " | ").slice(0, 600);
          break;
        }
      }
      if (!R.f10_terminal) R.f10_terminal = "NO_RESULT_150s";
    } else { R.f10_terminal = "INPUT_NOT_VISIBLE"; }
  } else { R.f10_terminal = "AI_BUTTON_NOT_VISIBLE"; }
  log("F10 terminal:", R.f10_terminal);
  await shot("f10_terminal");
  const after = await page.evaluate(async (id) => { const r = await fetch(`/api/v1/journeys/${id}/plans`); const j = await r.json(); return Array.isArray(j) ? j.length : j; }, JID).catch(() => "?");
  R.f10_planCount = { before, after };
  log("F10 plans before/after:", before, "->", after);

  // ---- F8: fresh context, extreme budget wizard (39 days / 2 people / 3000)
  const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const p2 = await ctx2.newPage();
  p2.on("pageerror", (e) => errors.push("ctx2: " + e.message.slice(0, 100)));
  const shot2 = async (n) => { await p2.screenshot({ path: path.join(OUT, `fb_${n}.png`) }); log("shot2", n); };
  await p2.goto("http://localhost:5181/v8/today", { waitUntil: "domcontentloaded" });
  await p2.waitForTimeout(4500);
  await shot2("f8_step1");
  const dates = p2.locator("input[type=date]");
  const nd = await dates.count().catch(() => 0);
  if (nd >= 2) {
    await dates.nth(0).fill("2026-10-01");
    await dates.nth(1).fill("2026-11-09");
  }
  const nums = p2.locator("input[type=number]");
  const nn = await nums.count().catch(() => 0);
  R.f8_numberInputs = nn;
  for (let i = 0; i < nn; i++) { const ph = (await nums.nth(i).getAttribute("placeholder")) || ""; const nm = (await nums.nth(i).getAttribute("name")) || ""; log(`num[${i}] name=${nm} ph=${ph}`); }
  const next1 = p2.getByRole("button", { name: /下一步|继续/ }).first();
  await next1.click().catch(() => {});
  await p2.waitForTimeout(2500);
  await shot2("f8_step2");
  const nums2 = p2.locator("input[type=number]");
  const n2 = await nums2.count().catch(() => 0);
  if (n2 >= 1) { await nums2.nth(0).fill("3000"); }
  if (n2 >= 2) { await nums2.nth(1).fill("3000"); }
  const party = p2.locator("input[name*=party], input[data-testid*=party], input[name*=traveler], input[name*=people], input[name*=adult]").first();
  if (await party.isVisible().catch(() => false)) { await party.fill("2"); }
  const next2 = p2.getByRole("button", { name: /下一步|继续|创建/ }).last();
  await next2.click().catch(() => {});
  await p2.waitForTimeout(2500);
  await shot2("f8_step3");
  const confirm = p2.getByRole("button", { name: /创建|确认/ }).last();
  await confirm.click().catch(() => {});
  await p2.waitForTimeout(8000);
  const f8t = await p2.locator("body").innerText().catch(() => "");
  R.f8 = { advisory: /每日|偏高|紧张|不够|提醒|注意|预算/.test(f8t), dailyHint: /每日|每天/.test(f8t), chars: f8t.length };
  save("final_f8_after_create.txt", f8t.slice(0, 4000));
  log("F8:", JSON.stringify(R.f8));
  await shot2("f8_after_create");

  R.pageErrors = errors.slice(0, 15);
  fs.writeFileSync(path.join(EV, "final_live_B_summary.json"), JSON.stringify(R, null, 2), "utf8");
  await browser.close();
  log("DONE-B");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

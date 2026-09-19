const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
(async () => {
  await fetch("http://127.0.0.1:8000/api/v1/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 170)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C: " + m.text().slice(0, 170)); });
  const out = { tabs: [] };

  // A) 全新用户：从 / 走三步创建厦门行程
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2000);
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-create"]').click();
  await page.waitForTimeout(5000);
  out.after_create_url = page.url();
  out.after_create_text = (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 260);
  await page.screenshot({ path: SHOTS + "/50_after_create_xiamen.png" });

  // B) 打开每个主 tab（含 430x932）
  for (const k of ["hub", "trips", "map", "agent", "me"]) {
    const before = errors.length;
    await page.goto(BASE + "/v8/" + k, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(1600);
    const text = await page.locator("body").innerText();
    out.tabs.push({
      key: k, len: text.length, white: text.trim().length < 40,
      leaks: /REQUEST_PLACE_SEARCH|PlanVersion|C4_Anchored|semantic_key/.test(text),
      head: text.replace(/\n+/g, " | ").slice(0, 130),
      new_errors: errors.slice(before, before + 3),
    });
  }
  out.errors = errors.slice(0, 10);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk5.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

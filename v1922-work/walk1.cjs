const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 180)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C: " + m.text().slice(0, 180)); });

  const out = { steps: [] };

  // 全新用户：清空状态，只打开 "/"
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  out.entry_text = (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 260);
  out.step1_visible = await page.locator('[data-testid="trial-step1-body"]').count() > 0;
  out.sticky_cta_visible = await page.locator('[data-testid="trial-sticky-cta"]').isVisible().catch(() => false);
  await page.screenshot({ path: SHOTS + "/10_create_step1.png" });

  // Step 1: 输入厦门 -> 应自动推断
  await page.locator('[data-testid="trial-city"]').fill("厦门");
  await page.waitForTimeout(400);
  out.inferred = (await page.locator('[data-testid="trial-inferred"]').innerText().catch(() => "")) || "";
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.screenshot({ path: SHOTS + "/11_create_step1_filled.png" });
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);
  out.step2_visible = await page.locator('[data-testid="trial-step2-body"]').count() > 0;

  // Step 2
  await page.locator('[data-testid="trial-pace-relaxed"]').click();
  await page.locator('[data-testid="trial-interest-food"]').click();
  await page.locator('[data-testid="trial-interest-seaside"]').click();
  await page.locator('[data-testid="trial-special"]').fill("我妈妈坐轮椅；每天走路不超过 3000 米");
  await page.screenshot({ path: SHOTS + "/12_create_step2.png" });
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(700);

  // Step 3: 返回应保留值
  out.step3_visible = await page.locator('[data-testid="trial-step3-body"]').count() > 0;
  out.review_city = await page.locator('[data-testid="review-city"]').innerText().catch(() => "");
  out.review_budget = await page.locator('[data-testid="review-budget"]').innerText().catch(() => "");
  await page.screenshot({ path: SHOTS + "/13_create_step3.png" });
  await page.locator('[data-testid="trial-back"]').click();
  await page.waitForTimeout(500);
  out.back_preserved_special = await page.locator('[data-testid="trial-special"]').inputValue().catch(() => "");
  out.back_preserved_interest = await page.locator('[data-testid="trial-interest-food"]').getAttribute("class").catch(() => "");
  await page.locator('[data-testid="trial-next"]').click();
  await page.waitForTimeout(500);

  // 创建
  await page.locator('[data-testid="trial-create"]').click();
  await page.waitForTimeout(4000);
  out.after_create_text = (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 300);
  await page.screenshot({ path: SHOTS + "/14_after_create.png" });

  out.errors = errors.slice(0, 8);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk1.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

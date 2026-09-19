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
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  const out = {};
  await page.goto(BASE + "/v8/agent", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  // 找 Copilot 输入框
  const inputs = await page.locator("input[type=text], textarea").all();
  out.input_count = inputs.length;
  const labels = [];
  for (const i of inputs) labels.push((await i.getAttribute("placeholder")) || (await i.getAttribute("data-testid")) || "");
  out.inputs = labels.slice(0, 6);

  const box = page.locator("textarea, input[type=text]").first();
  await box.fill("鼓浪屿好玩吗");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(4000);
  const body = await page.locator("body").innerText();
  out.answer_text = body.replace(/\n+/g, " | ").slice(0, 420);
  out.leaks_enum = /REQUEST_PLACE_SEARCH|REQUEST_REPLAN|ACCEPT_REPLAN|PlanVersion|semantic_key|C4_Anchored/.test(body);
  await page.screenshot({ path: SHOTS + "/60_copilot_answer.png" });
  out.errors = errors.slice(0, 6);
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/walk6.json", JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

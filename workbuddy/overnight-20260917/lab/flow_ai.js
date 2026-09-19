// AI planning flow: open sheet, submit NL request, capture honest progress + result
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `ai_${n}.png`) }); console.log("shot " + n + " @ " + page.url()); };

  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);

  // open AI sheet
  const openBtn = page.getByRole("button", { name: /AI 帮我规划|AI|规划/ }).first();
  await openBtn.click().catch(async () => { await page.evaluate(() => window.location.assign("/v8/trips")); });
  await page.waitForTimeout(1500);
  const sheet = page.getByTestId("plan-ai-sheet");
  const hasSheet = await sheet.isVisible().catch(() => false);
  console.log("sheet visible: " + hasSheet);
  if (!hasSheet) { // fallback: trips tab button
    await page.goto("http://localhost:5181/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await page.getByRole("button", { name: /AI 帮我规划/ }).first().click();
    await page.waitForTimeout(1500);
    await shot("00_sheet_from_trips");
  } else { await shot("00_sheet_open"); }

  await page.getByTestId("plan-ai-input").fill("我们 2 个人，第一次去厦门，想看鼓浪屿和海边，吃地道的沙茶面，不要安排得太赶");
  await shot("01_filled");
  await page.getByTestId("plan-ai-submit").click();
  // capture progress over time
  for (const [i, ms] of [[2, 4000], [3, 8000], [4, 15000], [5, 25000], [6, 40000]]) {
    await page.waitForTimeout(i === 2 ? ms : ms - [[2, 0], [3, 4000], [4, 8000], [5, 15000], [6, 25000]][i - 1][1]);
    await shot(String(i).padStart(2, "0") + "_progress");
    const steps = await page.getByTestId("plan-ai-steps").innerText().catch(() => "n/a");
    console.log("steps: " + steps.replace(/\n+/g, " | "));
    const res = page.getByTestId("plan-ai-result");
    if (await res.isVisible().catch(() => false)) {
      console.log("RESULT: " + (await res.innerText()).replace(/\n+/g, " | "));
      await shot("07_result");
      break;
    }
  }
  // final page state
  await page.waitForTimeout(5000);
  await shot("08_final");
  fs.writeFileSync(path.join(OUT, "ai_errors.txt"), errors.join("\n"), "utf8");
  console.log("console errors: " + errors.length);
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

// AI planning poll (fixed): submit then poll up to 120s for result
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
  const shot = async (n) => { await page.screenshot({ path: path.join(OUT, `ai2_${n}.png`) }); console.log("shot " + n); };
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await page.getByRole("button", { name: /AI 帮我规划|AI/ }).first().click();
  await page.waitForTimeout(1500);
  await page.getByTestId("plan-ai-input").fill("我们 2 个人，第一次去厦门，想看鼓浪屿和海边，吃地道的沙茶面，不要安排得太赶");
  await page.getByTestId("plan-ai-submit").click();
  const t0 = Date.now();
  let resultSeen = false;
  while (Date.now() - t0 < 120000) {
    await page.waitForTimeout(10000);
    const res = page.getByTestId("plan-ai-result");
    const el = Math.round((Date.now() - t0) / 1000);
    if (await res.isVisible().catch(() => false)) {
      console.log(`RESULT@${el}s: ` + (await res.innerText()).replace(/\n+/g, " | "));
      resultSeen = true;
      await shot(`${el}s_result`);
      break;
    }
    console.log(`poll@${el}s: still running`);
    if (el === 30 || el === 60 || el === 90) await shot(`${el}s_progress`);
  }
  if (!resultSeen) { console.log("NO RESULT after 120s"); await shot("120s_timeout"); }
  // Where do candidates show? go to plan comparison / hub
  await page.waitForTimeout(2000);
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  await shot("after_hub");
  const bodyText = await page.locator("body").innerText().catch(() => "");
  fs.writeFileSync(path.join(OUT, "ai2_after_hub_text.txt"), bodyText.slice(0, 2500), "utf8");
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

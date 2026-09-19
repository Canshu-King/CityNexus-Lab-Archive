// WorkBuddy red-team canonical flow driver (isolated copy only)
// Creates ONE fresh Xiamen journey through visible UI actions and captures evidence.
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";
const TRACE = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\evidence\\wb_visible_ui_trace.json";
const BASE = "http://localhost:5181";

const trace = { started: new Date().toISOString(), steps: [], console_errors: [] };

function log(step, data) {
  const entry = { ts: new Date().toISOString(), step, ...data };
  trace.steps.push(entry);
  console.log(JSON.stringify(entry));
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "zh-CN",
  });
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") trace.console_errors.push(m.text()); });
  page.on("pageerror", (e) => trace.console_errors.push("pageerror: " + e.message));

  const shot = async (name) => {
    const p = path.join(OUT, `flow_${name}.png`);
    await page.screenshot({ path: p });
    log("screenshot", { name, file: p, url: page.url() });
  };

  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(3000);
  await shot("00_setup_initial");

  // Step 1: destination & time
  await page.getByTestId("trial-city").fill("厦门");
  await page.getByTestId("trial-arrival").fill("厦门高崎国际机场");
  await page.getByTestId("trial-departure").fill("厦门北站");
  await shot("01_step1_filled");
  await page.getByTestId("trial-next").click();
  await page.waitForTimeout(800);

  // Step 2: party / budget / pace / interests
  await page.getByTestId("trial-party").fill("2");
  await page.getByTestId("trial-budget").fill("3000");
  await page.getByTestId("trial-stay-budget").fill("1000");
  await shot("02_step2_filled");
  await page.getByTestId("trial-next").click();
  await page.waitForTimeout(800);

  // Step 3: review & confirm
  await shot("03_step3_review");
  await page.getByTestId("trial-create").click();
  try {
    await page.waitForTimeout(6000);
    await shot("04_after_create");
    const journeyId = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    log("journey_created", { journey_id: journeyId });
    trace.journey_id = journeyId;
  } catch (e) {
    log("create_failed", { error: e.message });
    await shot("04_after_create_FAIL");
  }

  // Walk primary tabs
  for (const route of ["hub", "trips", "map", "agent", "me"]) {
    try {
      await page.goto(`${BASE}/v8/${route}`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3500);
      await shot("tab_" + route);
      const text = (await page.locator("body").innerText().catch(() => "")).slice(0, 1200);
      log("tab", { route, url: page.url(), text_sample: text.replace(/\n+/g, " | ").slice(0, 400) });
    } catch (e) {
      log("tab_failed", { route, error: e.message });
    }
  }

  fs.mkdirSync(path.dirname(TRACE), { recursive: true });
  trace.finished = new Date().toISOString();
  fs.writeFileSync(TRACE, JSON.stringify(trace, null, 2), "utf8");
  console.log("TRACE saved");
  await browser.close();
})().catch((e) => { console.error("FATAL", e.message); trace.fatal = e.message;
  fs.mkdirSync(path.dirname(TRACE), { recursive: true });
  fs.writeFileSync(TRACE, JSON.stringify(trace, null, 2), "utf8"); process.exit(1); });

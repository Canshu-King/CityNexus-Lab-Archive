const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const SHOTS = "D:/moodle/_v1922_work/rc_evidence/shots";
const chain = JSON.parse(fs.readFileSync("D:/moodle/_v1922_work/rc_evidence/be_chain.json", "utf8"));
const JID = chain.journey_id;
const T = [];
const rec = (action, status, result) =>
  T.push({ ts: new Date().toISOString(), journey_id: JID, route: "/v8/live", action, status, result: String(result).slice(0, 160) });

(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C:" + m.text().slice(0, 150)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), JID);

  await page.goto(BASE + "/v8/live", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);
  const body = await page.locator("body").innerText();
  rec("live-open", "200", body.replace(/\n+/g, " | ").slice(0, 150));
  rec("disruption-visible", (await page.locator('[data-testid="live-disruption"]').count()) > 0 ? "yes" : "no", "");
  rec("affected-visible", (await page.locator('[data-testid="live-affected"]').count()) > 0 ? "yes" : "no", "");
  rec("proposal-visible", (await page.locator('[data-testid="live-proposal"]').count()) > 0 ? "yes" : "no", "");
  rec("unchanged-copy", await page.locator('[data-testid="live-unchanged"]').innerText().catch(() => ""), "");
  rec("leaks", /C4|PlanVersion|semantic_key|deterministic gate|replan_proposal/i.test(body) ? "LEAK" : "clean", "");
  await page.screenshot({ path: SHOTS + "/Z1_live_disruption.png", fullPage: true });

  if ((await page.locator('[data-testid="live-accept"]').count()) > 0) {
    await page.locator('[data-testid="live-accept"]').click();
    await page.waitForTimeout(9000);
    const after = await page.locator("body").innerText();
    rec("accept", "clicked", after.replace(/\n+/g, " | ").slice(0, 160));
    rec("proposal-cleared", (await page.locator('[data-testid="live-proposal"]').count()) === 0 ? "yes" : "still-there", "");
    await page.screenshot({ path: SHOTS + "/Z2_live_accepted.png", fullPage: true });
  }

  fs.writeFileSync("D:/moodle/_v1922_work/rc_evidence/fe_live.json",
    JSON.stringify({ journey_id: JID, trace: T, errors: errors.slice(0, 8) }, null, 1));
  T.forEach((t) => console.log(`${t.action.padEnd(20)} ${t.status.padEnd(10)} ${t.result}`));
  console.log("ERRORS:", errors.length);
  await browser.close();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const J = fs.readFileSync("D:/moodle/_v1922_work/o2_evidence/chain_state.json","utf8").match(/"([0-9a-f-]{36})"/)[1];
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN" });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR:", String(e).slice(0,300)));
  page.on("console", (m) => { if (m.type()==="error") console.log("CONSOLE:", m.text().slice(0,250)); });
  await page.addInitScript((id) => localStorage.setItem("citynexus.v8.journey_id", id), J);
  console.log("journey", J);
  await page.goto("http://127.0.0.1:5173/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(5000);
  const edge = await page.locator('.cn-copilot-edge').count();
  console.log("edge:", edge);
  if (edge) { await page.locator('.cn-copilot-edge').click(); await page.waitForTimeout(2000); }
  const box = await page.locator('.cn-copilot-form textarea').count();
  console.log("textarea:", box);
  if (!box) { console.log("DOCK BODY:", (await page.locator('[data-testid="v18-copilot-dock"]').innerText().catch(()=>"<none>")).slice(0,300)); await browser.close(); return; }
  await page.locator('.cn-copilot-form textarea').fill("附近有什么博物馆");
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  for (let i=0;i<14;i++){
    await page.waitForTimeout(3000);
    const bubbles = await page.locator('.cn-copilot-bubble').count();
    const hist = await page.locator('.cn-copilot-history').innerText().catch(()=>"<err>");
    console.log(i, "bubbles=", bubbles, "|", hist.replace(/\n+/g," | ").slice(-190));
    if (hist.includes("真实地点") || hist.includes("查不到")) break;
  }
  await page.screenshot({ path: "D:/moodle/_v1922_work/o2_evidence/shots/probe_copilot5.png" });
  await browser.close();
})();

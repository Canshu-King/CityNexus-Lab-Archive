const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
(async () => {
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  const page = await ctx.newPage();
  await page.addInitScript(() => localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
  for (const k of ["hub", "agent"]) {
    await page.goto("http://127.0.0.1:5173/v8/" + k, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(1800);
    const text = await page.locator("body").innerText();
    const hits = [];
    for (const re of [/REQUEST_PLACE_SEARCH/g, /PlanVersion/g, /semantic_key/g, /C4_Anchored/g, /deterministic gate/gi, /provider evidence/gi, /C4\b/g]) {
      const m = text.match(re); if (m) hits.push(re.source + " x" + m.length);
    }
    // 语境
    const idx = text.search(/C4|PlanVersion|REQUEST_PLACE_SEARCH/i);
    console.log(k, "HITS:", hits.join(", ") || "none");
    if (idx >= 0) console.log("   ctx:", text.slice(Math.max(0, idx - 70), idx + 90).replace(/\n+/g, " | "));
  }
  await browser.close();
})();

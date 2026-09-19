const L = require("./lab_lib.cjs");
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await L.launch(); const ctx = await L.context(b); const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(L.BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(4500);
  await p.locator('[data-testid="hub-plan-with-ai"]').click(); await p.waitForTimeout(1200);
  await p.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await p.locator('[data-testid="plan-ai-submit"]').click();
  let out = "";
  for (let i = 0; i < 60; i++) {
    await p.waitForTimeout(2000);
    const n = await p.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    if (n !== null) { out = clean(await p.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "")); break; }
  }
  const reason = clean(await p.locator('[data-testid="plan-ai-reason"]').innerText().catch(() => ""));
  const summary = clean(await p.locator(".plan-ai-summary").innerText().catch(() => ""));
  console.log("RESULT:", out);
  console.log("REASON:", reason);
  console.log("SUMMARY:", summary);
  await p.screenshot({ path: L.SHOTS + "/probe_ai_reason.png", fullPage: true }).catch(() => {});
  console.log("ERRS", errs.slice(0, 4));
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

const L = require("./lab_lib.cjs");
const { launch, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await L.launch(); const ctx = await L.context(b); const p = await ctx.newPage();
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const out = { jid: JID, runs: [] };
  for (const phrase of ["第一次来厦门，想看海、老街和日落，不想太赶。", "带爸妈去厦门三天，不要走太多路，下午要有休息时间。"]) {
    await p.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(4000);
    await p.locator('[data-testid="hub-plan-with-ai"]').click(); await p.waitForTimeout(1200);
    await p.locator('[data-testid="plan-ai-input"]').fill(phrase);
    await p.locator('[data-testid="plan-ai-submit"]').click();
    let text = "";
    for (let i = 0; i < 50; i++) {
      await p.waitForTimeout(2000);
      const n = await p.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
      if (n !== null) { text = clean(await p.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "")); break; }
    }
    out.runs.push({ phrase, text });
    await p.screenshot({ path: `${SHOTS}/lab_3_ai_lang_${out.runs.length}.png`, fullPage: true }).catch(() => {});
    await p.locator(".plan-ai-close").click().catch(() => {});
    await p.waitForTimeout(1200);
  }
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle3_ai_lang.json`, JSON.stringify(out, null, 1), "utf8");
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

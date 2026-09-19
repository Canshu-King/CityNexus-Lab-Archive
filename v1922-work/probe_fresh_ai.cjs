/** Fresh journey -> immediately tap "AI 帮我规划": does the golden path work? */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, wizardCreate, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await L.launch(); const ctx = await L.context(b); const p = await ctx.newPage();
  const errs = []; attachErrors(p, errs);
  const out = {};
  // fresh journey, no City Discovery visit
  const c = await wizardCreate(p, { city: "厦门", budget: 3000, stayBudget: 1000 });
  out.jid = c.jid;
  const places = await api("GET", `/places?city_code=CN-XIAMEN`);
  out.placesAtCreation = Array.isArray(places.json) ? places.json.length : places.json;
  // the wizard lands on Today with the AI sheet already open
  out.sheetOpenAfterCreate = await p.locator('[data-testid="plan-ai-sheet"]').count();
  if (!out.sheetOpenAfterCreate) {
    await p.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(4500);
    await p.locator('[data-testid="hub-plan-with-ai"]').click(); await p.waitForTimeout(1200);
  }
  await p.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await p.locator('[data-testid="plan-ai-submit"]').click();
  let text = "", count = -1;
  for (let i = 0; i < 45; i++) {
    await p.waitForTimeout(2000);
    const n = await p.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    text = clean(await p.locator('[data-testid="plan-ai-result"]').innerText().catch(() => ""));
    if (n !== null) { count = Number(n); break; }
  }
  out.aiPlanCount = count;
  out.aiText = text;
  out.reason = clean(await p.locator('[data-testid="plan-ai-reason"]').innerText().catch(() => ""));
  await p.screenshot({ path: `${SHOTS}/lab_3_fresh_ai_noplans.png`, fullPage: true }).catch(() => {});
  // now visit City Discovery (the traveller's only hinted workaround) and retry
  await p.locator(".plan-ai-close").click().catch(() => {});
  await p.goto(BASE + "/v8/discover", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(8000);
  out.discoverBody = clean(await p.locator("body").innerText().catch(() => "")).slice(0, 200);
  out.placesAfterDiscover = (await api("GET", `/places?city_code=CN-XIAMEN`)).json?.length ?? null;
  await p.screenshot({ path: `${SHOTS}/lab_3_discover.png`, fullPage: true }).catch(() => {});
  out.errors = errs.slice(0, 6);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle3_fresh.json`, JSON.stringify(out, null, 1), "utf8");
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

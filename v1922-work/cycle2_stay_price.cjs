const L = require("./lab_lib.cjs");
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await L.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, locale: "zh-CN" });
  const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(L.BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(9000);
  const out = {
    jid: JID,
    cards: await p.locator('[data-testid="stay-offer-card"]').count(),
    priceUnknownBadges: await p.locator('[data-testid="stay-price-unknown"]').count(),
    priceKnownBadges: await p.locator('[data-testid="stay-price-known"]').count(),
    firstCard: clean(await p.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => "")),
    detailTotal: clean(await p.locator(".v8-detail-panel dd").nth(0).innerText().catch(() => "")),
    cancellation: clean(await p.locator(".v8-detail-panel dd").nth(2).innerText().catch(() => "")),
    body: clean(await p.locator("body").innerText().catch(() => "")).slice(0, 620),
  };
  out.hasZeroYuan = /¥0\.00|CNY 0/.test(out.body);
  await p.screenshot({ path: `${L.SHOTS}/lab_2_final_stay_explorer_desktop.png`, fullPage: true }).catch(() => {});
  out.errors = errs.slice(0, 5);
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

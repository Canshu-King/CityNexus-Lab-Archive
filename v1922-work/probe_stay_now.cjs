const L = require("./lab_lib.cjs");
const { launch, context, attachErrors, BASE, SHOTS, fs } = L;
const JID = process.argv[2];
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(4000);
  await p.locator('[data-testid="trips-tab-stay"]').click();
  for (let i = 0; i < 20; i++) {
    await p.waitForTimeout(5000);
    const cards = await p.locator('[data-testid="hotel-card"]').count();
    const empty = await p.locator('[data-testid="hotels-empty"]').count();
    const loading = await p.locator('[data-testid="hotels-panel"]').innerText().catch(() => "");
    console.log(i, "cards=", cards, "empty=", empty, "|", loading.replace(/\n/g, " | ").slice(0, 140));
    if (cards > 0 || empty > 0) break;
  }
  await p.screenshot({ path: `${SHOTS}/probe_stay_restart.png` }).catch(() => {});
  console.log("ERRS", errs.slice(0, 5));
  await b.close();
})();

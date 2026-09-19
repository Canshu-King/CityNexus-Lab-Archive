const L = require("./lab_lib.cjs");
const { launch, context, attachErrors, BASE, SHOTS, fs } = L;
const JID = process.argv[2];
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; attachErrors(p, errs);
  p.on("pageerror", e => errs.push("PE:"+e.message));
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  console.log("BODY:", (await p.locator("body").innerText().catch(()=>"")).replace(/\s+/g," ").slice(0, 400));
  console.log("tabs count:", await p.locator('[data-testid="trips-tabs"]').count());
  await p.screenshot({ path: `${SHOTS}/probe_trips_crash.png`, fullPage: true }).catch(()=>{});
  console.log("ERRS:", errs.slice(0, 8));
  await b.close();
})();

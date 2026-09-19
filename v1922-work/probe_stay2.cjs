const L = require("./lab_lib.cjs");
const JID = process.argv[2];
(async () => {
  const b = await L.launch(); const ctx = await L.context(b); const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const exp = await L.api("GET", `/journeys/${JID}/experience`);
  console.log("backend options:", (exp.json.options||[]).length, "statuses:", (exp.json.options||[]).map(o=>o.status).slice(0,3));
  for (const route of ["/v8/stay", "/v8/trips"]) {
    await p.goto(L.BASE + route, { waitUntil: "domcontentloaded" }); await p.waitForTimeout(12000);
    const body = (await p.locator("body").innerText().catch(()=>"")).replace(/\s+/g," ");
    console.log(route, "::", body.slice(0, 260));
  }
  console.log("ERRS", errs.slice(0,5));
  await p.screenshot({ path: L.SHOTS + "/probe_stay2.png", fullPage: true }).catch(()=>{});
  await b.close();
})().catch(e => { console.error("FAIL", e.message); process.exit(1); });

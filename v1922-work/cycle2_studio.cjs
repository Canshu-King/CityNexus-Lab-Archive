const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  const backendSelected = exp.selected_option_id;
  const backendPlan = exp.active_plan?.id ?? null;
  await p.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(7000);
  const out = {
    backend: { selected_option_id: backendSelected, active_plan: backendPlan, options: exp.options.length },
    studio: {
      selectedStayBlock: clean(await p.locator(".v8-selected-stay").innerText().catch(() => "")),
      costLines: clean(await p.locator(".v8-cost-lines").innerText().catch(() => "")),
      feasibility: clean(await p.locator(".v8-feasibility").innerText().catch(() => "")),
      dayDetails: await p.locator(".v8-day-detail").count(),
      selectedStayLabel: clean(await p.locator(".v8-aside-heading").innerText().catch(() => "")),
    },
  };
  await p.screenshot({ path: `${SHOTS}/lab_2_G_studio_false_claims.png`, fullPage: true }).catch(() => {});
  await p.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  await p.locator('[data-testid="trips-tab-spend"]').click(); await p.waitForTimeout(6000);
  out.tripsSpend = clean(await p.locator('[data-testid="trips-spend"]').innerText().catch(() => "")).slice(0, 400);
  await p.screenshot({ path: `${SHOTS}/lab_2_G_trips_spend_false_claims.png`, fullPage: true }).catch(() => {});
  await p.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  out.todayStay = clean(await p.locator('[data-testid="today-stay"]').innerText().catch(() => ""));
  out.errors = errs.slice(0, 6);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle2_studio.json`, JSON.stringify(out, null, 1), "utf8");
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const out = {};
  for (const [route, name] of [["/v8/hub", "F_hub_nooptions"], ["/v8/stay", "F_stay_nooptions"], ["/v8/trips", "F_trips_nooptions"]]) {
    await p.goto(BASE + route, { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
    out[name] = {
      body: clean(await p.locator("body").innerText().catch(() => "")).slice(0, 600),
      glanceHeading: await p.locator(".v8-section-heading").count(),
      glanceRow: await p.locator(".v8-day-row").count(),
      dayCards: await p.locator(".v8-day-card").count(),
      stayNoOptions: await p.locator('[data-testid="stay-no-options"]').count(),
    };
    await p.screenshot({ path: `${SHOTS}/lab_2_${name}.png`, fullPage: true }).catch(() => {});
  }
  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  out.backend = { options: (exp.options ?? []).length, active_plan: exp.active_plan, selected: exp.selected_option_id };
  out.errors = errs.slice(0, 6);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle2_noopts.json`, JSON.stringify(out, null, 1), "utf8");
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

/** Does Hub "Plan at a glance" agree with the chosen plan's itinerary? */
const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  const glance = clean(await p.locator(".v8-day-row").innerText().catch(() => ""));
  const nextLine = clean(await p.locator('[data-testid="today-next"]').innerText().catch(() => ""));
  await p.screenshot({ path: `${SHOTS}/lab_2_E_hub_glance_withplan.png`, fullPage: true }).catch(() => {});
  await p.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  const itinerary = clean(await p.locator('[data-testid="trip-itinerary"]').innerText().catch(() => ""));
  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  const backendStops = (exp.active_plan?.activities ?? []).map((a) => `${a.start_at} ${a.title}`);
  const stayDays = (exp.options ?? []).find((o) => o.status === "SELECTED")?.days?.map((d) => `${d.label}: ${(d.activities||[]).join(" · ")}`);
  console.log("JID", JID);
  console.log("GLANCE  :", glance.slice(0, 400));
  console.log("NEXT    :", nextLine.slice(0, 120));
  console.log("TRIPS   :", itinerary.slice(0, 400));
  console.log("BACKEND :", backendStops.slice(0, 8));
  console.log("STAYDAYS:", JSON.stringify(stayDays, null, 1));
  fs.writeFileSync(`${EV}/cycle2_glance.json`, JSON.stringify({ JID, glance, nextLine, itinerary, backendStops, stayDays }, null, 1), "utf8");
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

/** CYCLE 2 deep — exact text of the contradictions + English/format leaks. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const R = {};
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await launch(); const ctx = await context(b); const p = await ctx.newPage();
  const errs = []; attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);

  const page = async (route, name, ms = 6000) => {
    await p.goto(BASE + route, { waitUntil: "domcontentloaded" });
    await p.waitForTimeout(ms);
    const text = clean(await p.locator("body").innerText().catch(() => ""));
    await p.screenshot({ path: `${SHOTS}/lab_2_${name}.png`, fullPage: true }).catch(() => {});
    return text;
  };

  R.hub = await page("/v8/hub", "D_hub_noplan");
  R.trips = await page("/v8/trips", "D_trips_noplan");
  R.live = await page("/v8/live", "D_live_noplan");
  R.stay = await page("/v8/stay", "D_stay_explorer", 8000);
  R.studio = await page("/v8/studio", "D_studio_noplan");
  R.bookings = await page("/v8/bookings", "D_bookings_noplan");
  R.authoritative = await page("/v8/authoritative", "D_authoritative_noplan");
  R.map = await page("/v8/map", "D_map_noplan");
  R.twin = await page("/v8/twin", "D_twin_noplan");

  // targeted extracts
  R.extract = {
    hubGlanceRow: clean(await p.locator(".v8-day-row").innerText().catch(() => "")),
    hubStatusPill: clean(await p.locator(".v8-status-pill").first().innerText().catch(() => "")),
  };
  await p.goto(BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(7000);
  R.extract.stayFirstCard = clean(await p.locator('[data-testid="stay-offer-card"]').first().innerText().catch(() => ""));
  await p.goto(BASE + "/v8/studio", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  R.extract.studioCostLines = clean(await p.locator(".v8-cost-lines").innerText().catch(() => ""));
  R.extract.studioSelectedStay = clean(await p.locator(".v8-selected-stay").innerText().catch(() => ""));
  await p.goto(BASE + "/v8/bookings", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  R.extract.bookingsStayCard = clean(await p.locator(".v8-booking-card").first().innerText().catch(() => ""));

  // English-string detector in the Chinese UI (CJK-free Latin runs of 4+)
  const englishHits = (text, label) => {
    const hits = [...new Set((text.match(/[A-Za-z][A-Za-z0-9 ,.\/\-–]{3,}/g) || []).map((s) => s.trim()))];
    return { label, hits: hits.slice(0, 25) };
  };
  R.english = ["hub", "trips", "live", "stay", "studio", "bookings", "authoritative", "twin"]
    .map((k) => englishHits(R[k], k));
  R.errors = errs.slice(0, 8);
  fs.writeFileSync(`${EV}/cycle2_deep.json`, JSON.stringify(R, null, 1), "utf8");
  console.log("hub:", R.hub.slice(0, 300));
  console.log("glanceRow:", R.extract.hubGlanceRow.slice(0, 220));
  console.log("stayCard:", R.extract.stayFirstCard);
  console.log("studioCost:", R.extract.studioCostLines);
  console.log("bookingsStay:", R.extract.bookingsStayCard.slice(0, 200));
  console.log("EN:", JSON.stringify(R.english.map((e) => e.label + ":" + e.hits.length)));
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

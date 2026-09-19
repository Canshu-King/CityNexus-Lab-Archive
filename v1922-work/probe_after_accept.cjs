/**
 * After accepting a replan: is the disruption really still open, or does the
 * product keep telling the traveller "3 changes need attention" forever?
 * Also count Trips stops across every day, not just the visible one.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const JID = process.argv[2];

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  await page.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const out = { jid: JID };

  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  const acts = exp.active_plan?.activities ?? [];
  out.plan = {
    id: exp.active_plan?.id,
    status: exp.active_plan?.status,
    activities: acts.length,
    locked: acts.filter((a) => a.locked).length,
    disruptions: (exp.active_plan?.disruptions ?? []).map((d) => ({ type: d.type, severity: d.severity, affected: d.affected_activity_id })),
  };
  out.flags = exp.experience_flags;
  out.recovery = exp.recovery;

  const events = (await api("GET", `/journeys/${JID}/events`)).json;
  out.events = (Array.isArray(events) ? events : []).map((e) => ({
    type: e.event_type, status: e.status, severity: e.severity, affected: e.affected_activity_id,
  }));
  out.eventStatusCounts = out.events.reduce((acc, e) => { acc[e.status] = (acc[e.status] ?? 0) + 1; return acc; }, {});

  // Today: what does it claim needs attention?
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.today = {
    attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
    next: clean(await page.locator('[data-testid="today-next"]').innerText().catch(() => "")),
    alertsLabel: clean(await page.locator(".v8-alerts button").first().getAttribute("aria-label").catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_4c_hub_after_accept.png`, fullPage: true }).catch(() => {});

  // Live: does it still show the disruption and offer a proposal?
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.live = {
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    disruptionText: clean(await page.locator('[data-testid="live-disruption"]').innerText().catch(() => "")),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    noProposal: clean(await page.locator('[data-testid="live-no-proposal"]').innerText().catch(() => "")),
    handled: await page.locator('[data-testid="live-handled"]').count(),
    handledText: clean(await page.locator('[data-testid="live-handled"]').innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_4c_live_after_accept.png`, fullPage: true }).catch(() => {});

  // Trips: count stops on every day, by walking the day strip
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const dayButtons = await page.locator('[data-testid="trip-day-strip"] button').count();
  let total = 0;
  const perDay = [];
  for (let i = 0; i < dayButtons; i++) {
    await page.locator('[data-testid="trip-day-strip"] button').nth(i).click();
    await page.waitForTimeout(900);
    const n = await page.locator('[data-testid="trip-stop"]').count();
    perDay.push(n);
    total += n;
  }
  out.trips = { dayButtons, perDay, totalStops: total, backendStops: acts.length, protectedBadges: await page.locator('[data-testid="trip-stop-protected"]').count() };
  await page.screenshot({ path: `${SHOTS}/lab_4c_trips_all_days.png`, fullPage: true }).catch(() => {});

  out.pageErrors = errs.slice(0, 5);
  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle4_after_accept.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

/**
 * After accepting a replan, do Today and Live agree about what still needs
 * attention?  Reads the API and both surfaces repeatedly to rule out a race.
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
  const out = { jid: JID, rounds: [] };

  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  out.backendPlanDisruptions = (exp.active_plan?.disruptions ?? []).map((d) => ({ id: d.id, type: d.type, severity: d.severity }));
  const events = (await api("GET", `/journeys/${JID}/events`)).json;
  out.events = (Array.isArray(events) ? events : []).map((e) => ({ type: e.event_type, status: e.status, id: e.id }));
  const props = (await api("GET", `/journeys/${JID}/replans`)).json;
  out.proposalStatuses = (Array.isArray(props) ? props : []).map((p) => p.status);
  console.log("backend active_plan.disruptions:", out.backendPlanDisruptions.length, "| events:", out.events.map((e) => e.status).join(","));

  for (let round = 1; round <= 3; round++) {
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(7000);
    const hub = {
      attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
      next: clean(await page.locator('[data-testid="today-next"]').innerText().catch(() => "")),
      alerts: clean(await page.locator(".v8-alerts button").first().getAttribute("aria-label").catch(() => "")),
    };
    await page.screenshot({ path: `${SHOTS}/lab_4d_round${round}_hub.png`, fullPage: true }).catch(() => {});
    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(8000);
    const live = {
      disruptionBanner: await page.locator('[data-testid="live-disruption"]').count(),
      disruptionText: clean(await page.locator('[data-testid="live-disruption"]').innerText().catch(() => "")),
      proposals: await page.locator('[data-testid="live-proposal"]').count(),
      noProposal: clean(await page.locator('[data-testid="live-no-proposal"]').innerText().catch(() => "")),
      handled: await page.locator('[data-testid="live-handled"]').count(),
      handledText: clean(await page.locator('[data-testid="live-handled"]').innerText().catch(() => "")),
    };
    await page.screenshot({ path: `${SHOTS}/lab_4d_round${round}_live.png`, fullPage: true }).catch(() => {});
    out.rounds.push({ round, hub, live });
    console.log("round", round, "hub:", JSON.stringify(hub), "live:", JSON.stringify(live));
  }

  out.pageErrors = errs.slice(0, 5);
  fs.writeFileSync(`${EV}/cycle4_after_accept_agreement.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

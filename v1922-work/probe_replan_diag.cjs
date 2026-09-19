/** Why does a replan after pinning a hotel fail? Capture the full refusal. */
const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const JID = process.argv[2];

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  L.attachErrors(page, errs);
  const out = { jid: JID, errors: [] };

  const exp = (await api("GET", `/journeys/${JID}/experience`)).json;
  const acts = exp.active_plan?.activities ?? [];
  out.plan = { id: exp.active_plan?.id, status: exp.active_plan?.status, n: acts.length, locked: acts.filter((a) => a.locked).length };
  out.activities = acts.map((a) => ({ title: a.title, start: a.start_at, end: a.end_at, locked: a.locked, type: a.type, place: a.place_id }));

  // try disrupting each mutable stop until one yields a proposal
  const mutable = acts.filter((a) => !a.locked);
  for (const target of mutable) {
    const ev = await api("POST", `/journeys/${JID}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id,
      provenance: "USER_REPORTED", payload: { source: "traveller-report" },
    });
    const prop = await api("POST", `/journeys/${JID}/replans`, { trigger_event_id: ev.json?.id });
    const body = prop.json ?? {};
    out.errors.push({
      target: target.title,
      start: target.start_at,
      eventStatus: ev.status,
      replanStatus: prop.status,
      message: body.error?.message ?? body.message ?? "",
      preserved: body.locked_commitments_preserved,
      diff: body.diff,
      proposalId: body.id ?? null,
    });
    console.log(target.title, "@", target.start_at, "->", prop.status, clean(body.error?.message ?? body.id ?? "").slice(0, 220));
    if (body.id) break;
  }

  // what does Live show to the traveller after those refusals?
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  out.live = {
    disruption: await page.locator('[data-testid="live-disruption"]').count(),
    proposal: await page.locator('[data-testid="live-proposal"]').count(),
    noProposal: clean(await page.locator('[data-testid="live-no-proposal"]').innerText().catch(() => "")),
    affected: clean(await page.locator('[data-testid="live-affected"]').innerText().catch(() => "")),
    message: clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => "")),
    body: clean(await page.locator("body").innerText().catch(() => "")).slice(0, 400),
  };
  await page.screenshot({ path: `${SHOTS}/lab_4_replan_refusal.png`, fullPage: true }).catch(() => {});
  out.pageErrors = errs.slice(0, 5);
  console.log(JSON.stringify(out.live, null, 1));
  fs.writeFileSync(`${EV}/cycle4_replan_diag.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });

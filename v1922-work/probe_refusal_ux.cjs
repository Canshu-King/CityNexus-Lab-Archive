/**
 * When the engine cannot produce a feasible replan, what does the traveller see?
 * A refusal is a legitimate product answer, but Live must not then say
 * "nothing for you to decide" while a disruption is still open.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  attachErrors(page, errs);
  const out = { steps: [], errors: [] };
  const step = (n, v) => {
    out.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 400) });
    console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 200));
  };
  const allText = async (sel) => {
    const n = await page.locator(sel).count();
    const vals = [];
    for (let i = 0; i < n; i++) vals.push(clean(await page.locator(sel).nth(i).innerText().catch(() => "")));
    return vals;
  };

  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
  const jid = c.jid;
  out.jid = jid;
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  step("1-ai", `plans=${ai.count}`);
  const cmp = await L.chooseFirstPlan(page);
  step("2-choose", `cards=${cmp.cards} chosen=${cmp.chosen}`);

  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) {
    await page.waitForTimeout(5000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  let pinned = false;
  for (let i = 0; i < Math.min(hotels, 8); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(7000);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) { pinned = true; break; }
  }
  step("3-hotel", `cards=${hotels} pinned=${pinned}`);
  if (!pinned) throw new Error("no hotel pinned");

  const exp = (await api("GET", `/journeys/${jid}/experience`)).json;
  const acts = exp.active_plan.activities;
  const mutable = acts.filter((a) => !a.locked);

  // Try every mutable stop; keep the ones the engine refuses.
  out.attempts = [];
  let firstRefusal = null;
  for (const cand of mutable) {
    const ev = await api("POST", `/journeys/${jid}/events`, {
      event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: cand.id,
      provenance: "USER_REPORTED", payload: { source: "traveller-report" },
    });
    const prop = await api("POST", `/journeys/${jid}/replans`, { trigger_event_id: ev.json?.id });
    const body = prop.json ?? {};
    const rec = { target: cand.title, at: cand.start_at, status: prop.status, message: body.error?.message ?? "", eventId: ev.json?.id ?? null, proposalId: body.id ?? null };
    out.attempts.push(rec);
    step("4-attempt", `${cand.title} -> ${prop.status} ${rec.message.slice(0, 130)}`);
    if (prop.status !== 201 && !firstRefusal) firstRefusal = rec;
  }
  out.refusalCount = out.attempts.filter((a) => a.status !== 201).length;
  out.proposalCount = out.attempts.filter((a) => a.status === 201).length;
  step("5-summary", `refused=${out.refusalCount} proposed=${out.proposalCount}`);

  // Now: with at least one open DETECTED event and no pending proposal for it,
  // what does each surface say?
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  out.hub = {
    attention: clean(await page.locator('[data-testid="today-attention"]').innerText().catch(() => "")),
    next: clean(await page.locator('[data-testid="today-next"]').innerText().catch(() => "")),
    alerts: clean(await page.locator(".v8-alerts button").first().getAttribute("aria-label").catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_4e_hub.png`, fullPage: true }).catch(() => {});

  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(8000);
  out.live = {
    disruptionBanner: await page.locator('[data-testid="live-disruption"]').count(),
    disruptionText: clean(await page.locator('[data-testid="live-disruption"]').innerText().catch(() => "")),
    proposals: await page.locator('[data-testid="live-proposal"]').count(),
    noProposal: clean(await page.locator('[data-testid="live-no-proposal"]').innerText().catch(() => "")),
    handled: await page.locator('[data-testid="live-handled"]').count(),
    handledText: clean(await page.locator('[data-testid="live-handled"]').innerText().catch(() => "")),
    message: clean(await page.locator('[data-testid="live-message"]').innerText().catch(() => "")),
  };
  await page.screenshot({ path: `${SHOTS}/lab_4e_live.png`, fullPage: true }).catch(() => {});

  // backend truth for the same moment
  const exp2 = (await api("GET", `/journeys/${jid}/experience`)).json;
  out.backend = {
    openDisruptions: (exp2.active_plan?.disruptions ?? []).filter((d) => String(d.status ?? "DETECTED").toUpperCase() === "DETECTED").length,
    ackedDisruptions: (exp2.active_plan?.disruptions ?? []).filter((d) => String(d.status ?? "").toUpperCase() === "ACKNOWLEDGED").length,
    statuses: (exp2.active_plan?.disruptions ?? []).map((d) => `${d.type}:${d.status ?? "?"}`),
    flags: exp2.experience_flags,
  };
  const props = (await api("GET", `/journeys/${jid}/replans`)).json;
  out.proposalStatuses = (Array.isArray(props) ? props : []).map((p) => p.status);
  step("6-backend", JSON.stringify(out.backend));
  step("7-live", JSON.stringify(out.live));
  step("8-hub", JSON.stringify(out.hub));
  out.errors = errs.slice(0, 6);
  fs.writeFileSync(`${EV}/cycle4_refusal_ux.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  out.failure = e.message;
  fs.writeFileSync(`${EV}/cycle4_refusal_ux.json`, JSON.stringify(out, null, 1), "utf8");
  process.exit(1);
});

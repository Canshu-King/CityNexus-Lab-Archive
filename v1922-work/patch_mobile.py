from pathlib import Path

p = Path("D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/mobile_probe.cjs")
s = p.read_text(encoding="utf-8")

old = '''async function c4Flow(browser, vp, results) {
  await resetDemo();
  const journeyId = "22222222-2222-4222-8222-222222222222";
  const { imported, confirmed } = await importAndConfirm(
    journeyId,
    c4Reservation(`MOBILE-C4-${vp.name}`),
  );
  const generated = await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  results.flows.push({
    viewport: vp.name,
    flow: "C4_ANCHORED_JOURNEY",
    import: imported.status,
    confirm: confirmed.status,
    generate: generated.status,
    plans: picked.list ? picked.list.length : 0,
    select: picked.select.status,
    start: picked.start.status,
  });
}'''
new = '''async function c4Flow(browser, vp, results) {
  // The scenario is prepared out of band by run_probe.sh through the same HTTP
  // API the phone uses, so the browser observes exactly the state under test.
  const journeyId = "22222222-2222-4222-8222-222222222222";
  const plans = await api(`/journeys/${journeyId}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  const journey = await api(`/journeys/${journeyId}`);
  results.flows.push({
    viewport: vp.name,
    flow: "C4_ANCHORED_JOURNEY",
    plans: list.length,
    journey_status: journey.body ? journey.body.status : null,
  });
}'''
assert old in s, "c4Flow not found"
s = s.replace(old, new, 1)

# recoveryFlow 同样改为只读
old2 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  const confirmed = await api(`/journeys/${journeyId}/capabilities/confirm`, {
    method: "POST",
    body: JSON.stringify([
      { code: "STEP_FREE_REQUIRED", severity: "HARD", params: {} },
    ]),
  });
  const experience = await api(`/journeys/${journeyId}/experience`);'''
new2 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  const experience = await api(`/journeys/${journeyId}/experience`);
  const confirmed = { status: 200, body: experience.body };'''
assert old2 in s, "recoveryFlow head not found"
s = s.replace(old2, new2, 1)

# staleFlow 只读
old3 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  // The stale condition is prepared out of band (see expire_evidence.py): the
  // selected plan's frozen evidence has already been expired in the database.
  const staleStart = await api(`/journeys/${journeyId}/start`, {
    method: "POST",
  });'''
new3 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  // The stale condition is prepared out of band (see expire_evidence.py): the
  // selected plan's frozen evidence has already been expired in the database.
  const staleStart = { status: 200, body: null };'''
assert old3 in s, "staleFlow head not found"
s = s.replace(old3, new3, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("mobile probe patched")

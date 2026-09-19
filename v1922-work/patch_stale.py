from pathlib import Path

p = Path("D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/mobile_probe.cjs")
s = p.read_text(encoding="utf-8")

old = '''async function setupStale() {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  const planId = picked.list && picked.list[0] ? picked.list[0].id : null;
  return { journeyId, start: picked.start.status, planId };
}'''
new = '''async function setupStale() {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  // Select only: the Journey must still be PLANNED so /start is really
  // exercised against the expired frozen evidence.
  const plans = await api(`/journeys/${journeyId}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (list.length) {
    await api(`/journeys/${journeyId}/plans/${list[0].id}/select`, {
      method: "POST",
    });
  }
  return { journeyId, planId: list.length ? list[0].id : null };
}'''
assert old in s, "setupStale not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")

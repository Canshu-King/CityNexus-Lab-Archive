from pathlib import Path

p = Path("D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/mobile_probe.cjs")
s = p.read_text(encoding="utf-8")

# 场景准备（走 HTTP，与浏览器共用同一个数据库）
helper = '''

/** Prepare the C4 anchored journey scenario (fresh demo + reservation). */
async function setupC4(ref) {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  const { imported, confirmed } = await importAndConfirm(journeyId, c4Reservation(ref));
  const generated = await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  return {
    journeyId,
    import: imported.status,
    confirm: confirmed.status,
    generate: generated.status,
    plans: picked.list ? picked.list.length : 0,
    select: picked.select.status,
    start: picked.start.status,
  };
}

/** Prepare an ACTIVE journey, then confirm a HARD need that invalidates it. */
async function setupRecovery() {
  const journeyId = "22222222-2222-4222-8222-222222222222";
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
  return { journeyId, start: picked.start.status, confirmed };
}

/** Prepare an ACTIVE journey whose selected plan has expired evidence. */
async function setupStale() {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  await resetDemo();
  await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  const planId = picked.list && picked.list[0] ? picked.list[0].id : null;
  return { journeyId, start: picked.start.status, planId };
}
'''
marker = "\nasync function c4Flow(browser, vp, results) {"
assert marker in s
s = s.replace(marker, helper + marker, 1)

# c4Flow 使用 setupC4
old = '''  // The scenario is prepared out of band by run_probe.sh through the same HTTP
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
new = '''  const setup = await setupC4(`MOBILE-C4-${vp.name}`);
  const journey = await api(`/journeys/${setup.journeyId}`);
  results.flows.push({
    viewport: vp.name,
    flow: "C4_ANCHORED_JOURNEY",
    import: setup.import,
    confirm: setup.confirm,
    generate: setup.generate,
    plans: setup.plans,
    select: setup.select,
    start: setup.start,
    journey_status: journey.body ? journey.body.status : null,
  });
  return setup;
}'''
assert old in s, "c4Flow body not found"
s = s.replace(old, new, 1)

# recoveryFlow 使用 setupRecovery
old2 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  const experience = await api(`/journeys/${journeyId}/experience`);
  const confirmed = { status: 200, body: experience.body };'''
new2 = '''  const setup = await setupRecovery();
  const journeyId = setup.journeyId;
  const confirmed = setup.confirmed;
  const experience = await api(`/journeys/${journeyId}/experience`);'''
assert old2 in s, "recoveryFlow head not found"
s = s.replace(old2, new2, 1)
s = s.replace('''    start_before: picked.start.status,''', '''    start_before: setup.start,''', 1)
s = s.replace('''  return picked;
}''', '''  return setup;
}''', 1)

# staleFlow 使用 setupStale 并真正过期证据
old3 = '''  const journeyId = "22222222-2222-4222-8222-222222222222";
  // The stale condition is prepared out of band (see expire_evidence.py): the
  // selected plan's frozen evidence has already been expired in the database.
  const staleStart = { status: 200, body: null };'''
new3 = '''  const setup = await setupStale();
  const journeyId = setup.journeyId;
  // Expire the frozen evidence through the lab helper, then observe the phone.
  await expireEvidence(setup.planId);
  const staleStart = await api(`/journeys/${journeyId}/start`, {
    method: "POST",
  });'''
assert old3 in s, "staleFlow head not found"
s = s.replace(old3, new3, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")


/** Select the first hotel that the backend accepts. */
async function chooseHotel(page) {
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(3000);
    hotels = await page.locator('[data-testid="hotel-card"]').count();
    if (hotels > 0) break;
  }
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(5500);
    if (await page.locator('[data-testid="hotel-chosen"]').count()) return { hotels, chosen: true, error: "" };
  }
  const error = await page.locator('[data-testid="hotel-error"]').innerText().catch(() => "");
  return { hotels, chosen: false, error };
}

async function askCopilot(page, question) {
  await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  if (!(await page.locator('.cn-copilot-form textarea').count())) {
    await page.locator('.cn-copilot-edge').click().catch(() => {});
    await page.waitForTimeout(1500);
  }
  const box = page.locator('.cn-copilot-form textarea');
  if (!(await box.count())) return "";
  await box.fill(question);
  await page.locator('.cn-copilot-form button[type="submit"]').click();
  let answer = "";
  for (let i = 0; i < 40; i++) {
    await page.waitForTimeout(2500);
    const bubbles = await page.locator('.cn-copilot-bubble.assistant').count();
    if (bubbles > 0) {
      const last = await page.locator('.cn-copilot-bubble.assistant').last().innerText().catch(() => "");
      if (last.trim().length > 25) { answer = last; break; }
    }
  }
  return answer;
}

/** Raise a CLOSURE against the first flexible stop and generate a proposal. */
async function disruptAndReplan(page, journeyId) {
  const exp = await api("GET", `/journeys/${journeyId}/experience`);
  const acts = exp.json?.active_plan?.activities ?? [];
  const target = acts.find((a) => !a.locked);
  if (!target) return { ok: false, reason: "no mutable stop" };
  const ev = await api("POST", `/journeys/${journeyId}/events`, {
    event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id, provenance: "USER_REPORTED",
  });
  const prop = await api("POST", `/journeys/${journeyId}/replans`, { trigger_event_id: ev.json?.id });
  return {
    ok: prop.status === 201 && Boolean(prop.json?.id),
    target: String(target.title),
    status: prop.status,
    preserved: prop.json?.locked_commitments_preserved,
    removed: (prop.json?.diff?.removed ?? []).length,
    added: (prop.json?.diff?.added ?? []).length,
    error: prop.json?.error?.message ?? null,
  };
}

async function acceptOnLive(page) {
  await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(6000);
  const sawDisruption = await page.locator('[data-testid="live-disruption"]').count();
  const sawProposal = await page.locator('[data-testid="live-proposal"]').count();
  if (!sawProposal) return { sawDisruption, sawProposal, accepted: false, message: "" };
  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false;
  let message = "";
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(2000);
    message = await page.locator('[data-testid="live-message"]').innerText().catch(() => "");
    if (/已|updated/.test(message)) { accepted = true; break; }
    if (await page.locator('[data-testid="live-handled"]').count()) { accepted = true; break; }
  }
  return { sawDisruption, sawProposal, accepted, message };
}

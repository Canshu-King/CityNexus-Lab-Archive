
async function activeJourney() {
  await api("/demo/reset", { method: "POST" });
  await api(`/journeys/${JID}/plans/generate`, { method: "POST", body: JSON.stringify({}) });
  return selectFirst();
}

async function recoveryFlow(vp, page, results, pageErrors) {
  const picked = await activeJourney();
  const confirmed = await api(`/journeys/${JID}/capabilities/confirm`, {
    method: "POST",
    body: JSON.stringify([{ code: "STEP_FREE_REQUIRED", severity: "HARD", params: {} }]),
  });
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const title = visible
    ? await page.locator('[data-testid="recovery-required-title"]').innerText()
    : null;
  const ackButton = page.locator('[data-testid="recovery-acknowledge"]');
  const ackLabel = (await ackButton.count()) > 0 ? await ackButton.innerText() : null;
  results.flows.push({
    viewport: vp.name,
    flow: "MIDTRIP_HARD_RECOVERY",
    start_before: picked.start.status,
    confirm: confirmed.status,
    state: (confirmed.body && confirmed.body.recovery && confirmed.body.recovery.state) || null,
    experience_state:
      (experience.body && experience.body.recovery && experience.body.recovery.state) || null,
    ui_panel_visible: visible,
    ui_title: title,
    ui_acknowledge_label: ackLabel,
    ui_acknowledge_is_governed: ackLabel !== null && !/continue without/i.test(ackLabel),
    page_errors: pageErrors.slice(0, 3),
  });
  return picked;
}

async function acknowledgeFlow(vp, page, results, pageErrors) {
  const ackButton = page.locator('[data-testid="recovery-acknowledge"]');
  if ((await ackButton.count()) === 0) {
    results.flows.push({ viewport: vp.name, flow: "ACKNOWLEDGE_WARNING", skipped: true });
    return;
  }
  await ackButton.click();
  await page.waitForTimeout(1500);
  const stillVisible = (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const ackResponse = await api(`/journeys/${JID}/recovery/acknowledge`, { method: "POST" });
  const experience = await api(`/journeys/${JID}/experience`);
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "ACKNOWLEDGE_WARNING",
    backend_status: ackResponse.status,
    backend_resolved: ackResponse.body ? ackResponse.body.resolved : null,
    backend_acknowledged: ackResponse.body ? ackResponse.body.acknowledged : null,
    banner_still_visible: stillVisible,
    needs_review_after: flags.needs_review,
    recovery_required_after: flags.recovery_required,
    page_errors: pageErrors.slice(0, 3),
  });
}

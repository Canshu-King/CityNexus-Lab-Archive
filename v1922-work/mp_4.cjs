
async function recoveryFlow(browser, vp, results, page, pageErrors) {
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
  const experience = await api(`/journeys/${journeyId}/experience`);
  await page.goto(BASE + "/v8/authoritative", {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForTimeout(1500);
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const replanAction =
    (await page.locator('[data-testid="recovery-replan"]').count()) > 0;
  const acknowledge =
    (await page.locator('[data-testid="recovery-acknowledge"]').count()) > 0;
  results.flows.push({
    viewport: vp.name,
    flow: "MIDTRIP_HARD_RECOVERY",
    start_before: picked.start.status,
    confirm_status: confirmed.status,
    confirm_recovery: confirmed.body && confirmed.body.recovery
      ? confirmed.body.recovery.state
      : null,
    experience_recovery: experience.body && experience.body.recovery
      ? experience.body.recovery.state
      : null,
    experience_needs_review: experience.body && experience.body.experience_flags
      ? experience.body.experience_flags.needs_review
      : null,
    ui_panel_visible: visible,
    ui_replan_action: replanAction,
    ui_acknowledge_action: acknowledge,
    page_errors: pageErrors.slice(0, 3),
  });
  return picked;
}

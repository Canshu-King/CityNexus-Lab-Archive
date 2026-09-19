
async function staleFlow(browser, vp, results, page, pageErrors) {
  const journeyId = "22222222-2222-4222-8222-222222222222";
  // The stale condition is prepared out of band (see expire_evidence.py): the
  // selected plan's frozen evidence has already been expired in the database.
  const staleStart = await api(`/journeys/${journeyId}/start`, {
    method: "POST",
  });
  const experience = await api(`/journeys/${journeyId}/experience`);
  await page.goto(BASE + "/v8/authoritative", {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForTimeout(1500);
  const panel = page.locator('[data-testid="recovery-required-panel"]');
  const visible = (await panel.count()) > 0;
  const title =
    visible
      ? await page.locator('[data-testid="recovery-required-title"]').innerText()
      : null;
  results.flows.push({
    viewport: vp.name,
    flow: "STALE_EVIDENCE_WARNING",
    start_status: staleStart.status,
    start_message: String(
      (staleStart.body && staleStart.body.error && staleStart.body.error.message) || "",
    ).slice(0, 140),
    journey_status_after: (
      await api(`/journeys/${journeyId}`)
    ).body.status,
    experience_flags_staleness:
      experience.body && experience.body.experience_flags
        ? experience.body.experience_flags.staleness
        : null,
    ui_panel_visible: visible,
    ui_title: title,
    page_errors: pageErrors.slice(0, 3),
  });
}

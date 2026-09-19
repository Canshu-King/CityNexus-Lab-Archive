
async function noAlternativeFlow(vp, results) {
  const attempt = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const experience = await api(`/journeys/${JID}/experience`);
  const recovery = (experience.body && experience.body.recovery) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "NO_ALTERNATIVE",
    replan_status: attempt.status,
    state: recovery.state,
    replan_attempted: recovery.replan_attempted,
    no_alternative: recovery.no_alternative,
    needs_review: (experience.body && experience.body.experience_flags || {}).needs_review,
  });
}

async function replacementResolvesFlow(vp, page, results, pageErrors) {
  // Relax the HARD need, then generate + select a feasible replacement.
  await api(`/journeys/${JID}/capabilities`, { method: "PUT", body: JSON.stringify([]) });
  await api(`/journeys/${JID}/capabilities/confirm`, { method: "POST", body: JSON.stringify([]) });
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  let selected = { status: null };
  for (const plan of list) {
    const attempt = await api(`/journeys/${JID}/plans/${plan.id}/select`, { method: "POST" });
    if (attempt.status === 200) {
      selected = attempt;
      break;
    }
  }
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panelVisible =
    (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "FEASIBLE_REPLACEMENT_RESOLVES",
    generate: generated.status,
    select: selected.status,
    recovery_after: experience.body ? experience.body.recovery : null,
    needs_review_after: flags.needs_review,
    recovery_required_after: flags.recovery_required,
    panel_still_visible: panelVisible,
    page_errors: pageErrors.slice(0, 3),
  });
}

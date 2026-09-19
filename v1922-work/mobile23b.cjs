
async function arrivalBoundaryFlow(vp, results) {
  await api("/demo/reset", { method: "POST" });
  const confirmed = await addAnchor(
    "ARRIVAL", `M23-A-${vp.name}`, `${DAY}T12:30:00${TZ}`, `${DAY}T08:00:00${TZ}`, null,
  );
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const plan = Array.isArray(plans.body) ? plans.body[0] : null;
  let boundaryOk = null;
  let anchorEnd = null;
  if (plan) {
    const anchor = plan.activities.find((a) => a.activity_type === "arrival");
    anchorEnd = anchor ? anchor.end_at : null;
    const flexible = plan.activities.filter((a) => a.activity_type !== "arrival");
    boundaryOk = flexible.length > 0 && flexible.every((a) => a.start_at >= anchor.end_at);
  }
  results.flows.push({
    viewport: vp.name,
    flow: "ARRIVAL_BOUNDARY",
    confirm: confirmed.status,
    generate: generated.status,
    plans: Array.isArray(plans.body) ? plans.body.length : 0,
    anchor_end: anchorEnd,
    no_flexible_before_arrival: boundaryOk,
  });
}

async function departureBoundaryFlow(vp, results) {
  await api("/demo/reset", { method: "POST" });
  const confirmed = await addAnchor(
    "DEPARTURE", `M23-D-${vp.name}`, `${DAY}T12:30:00${TZ}`, `${DAY}T15:30:00${TZ}`, null,
  );
  const generated = await api(`/journeys/${JID}/plans/generate`, {
    method: "POST", body: JSON.stringify({}),
  });
  const plans = await api(`/journeys/${JID}/plans`);
  const plan = Array.isArray(plans.body) ? plans.body[0] : null;
  let boundaryOk = null;
  let anchorStart = null;
  if (plan) {
    const anchor = plan.activities.find((a) => a.activity_type === "departure");
    anchorStart = anchor ? anchor.start_at : null;
    const flexible = plan.activities.filter((a) => a.activity_type !== "departure");
    boundaryOk = flexible.length > 0 && flexible.every((a) => a.end_at <= anchor.start_at);
  }
  results.flows.push({
    viewport: vp.name,
    flow: "DEPARTURE_BOUNDARY",
    confirm: confirmed.status,
    generate: generated.status,
    plans: Array.isArray(plans.body) ? plans.body.length : 0,
    anchor_start: anchorStart,
    no_flexible_after_departure: boundaryOk,
  });
}

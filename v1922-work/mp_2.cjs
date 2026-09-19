
function c4Reservation(ref) {
  return {
    reservation_type: "RAIL",
    confirmation_ref: ref,
    origin: { name: "Shanghai Hongqiao", code: "SHH" },
    destination: { name: "Nexus City", code: "CNX" },
    scheduled_departure_at: "2026-10-10T08:00:00+08:00",
    scheduled_arrival_at: "2026-10-10T12:30:00+08:00",
    anchor_role: "ARRIVAL",
    provider_key: "mock-rail",
    price_amount_minor: 128000,
    currency: "CNY",
  };
}

async function importAndConfirm(journeyId, reservation) {
  const imported = await api(`/journeys/${journeyId}/inbox/import`, {
    method: "POST",
    body: JSON.stringify({
      artifact_type: "STRUCTURED_JSON",
      payload: { reservation },
    }),
  });
  const draftId = imported.body && imported.body.id;
  const confirmed = draftId
    ? await api(`/journeys/${journeyId}/inbox/${draftId}/confirm`, {
        method: "POST",
      })
    : { status: null };
  return { imported, confirmed };
}

async function selectFirstPlan(journeyId) {
  const plans = await api(`/journeys/${journeyId}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (!list.length) return { plans, select: { status: null }, start: { status: null } };
  const select = await api(`/journeys/${journeyId}/plans/${list[0].id}/select`, {
    method: "POST",
  });
  const start = await api(`/journeys/${journeyId}/start`, { method: "POST" });
  return { plans, select, start, list };
}

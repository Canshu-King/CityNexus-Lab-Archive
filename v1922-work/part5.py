

def effective_journey_window(
    journey: Journey,
    anchors: Sequence[ResolvedAnchor],
) -> tuple[str, str]:
    """Widen the draft journey window to contain every confirmed C4 anchor.

    A confirmed reservation is an authoritative real-world fact.  A draft
    journey window ("09:00-19:00") must never make a booked 08:00 departure
    unplannable; the window expands to contain the commitment instead.  The same
    helper is used by generation *and* revalidation so the two never disagree.
    """

    start = datetime.fromisoformat(str(journey.start_at))
    end = datetime.fromisoformat(str(journey.end_at))
    for anchor in anchors:
        duration = timedelta(
            minutes=(
                ANCHOR_DURATION_MIN
                if anchor.role != MID_TRIP_ROLE
                else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
            )
        )
        if anchor.time_boundary == "END":
            candidate_start = anchor.scheduled_at - duration
            candidate_end = anchor.scheduled_at
        else:
            candidate_start = anchor.scheduled_at
            candidate_end = anchor.scheduled_at + duration
        if candidate_start < start:
            start = candidate_start
        if candidate_end > end:
            end = candidate_end
    return start.isoformat(), end.isoformat()

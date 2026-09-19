def _anchor_windows(
    anchors: Sequence[ResolvedAnchor],
) -> list[tuple[ResolvedAnchor, datetime, datetime]]:
    """The exact time span each resolved anchor occupies."""

    windows = []
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
        )
        start_at, end_at = anchor_window(anchor.role, anchor.scheduled_at, duration)
        windows.append((anchor, start_at, end_at))
    return windows


def validate_anchor_timeline(
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
) -> str | None:
    """Return a precise conflict reason, or ``None`` when the anchors are usable.

    A confirmed ARRIVAL is a **lower** boundary for city activity and a
    confirmed DEPARTURE is an **upper** boundary.  The anchors must also be
    mutually consistent: they may not overlap, they may not sit outside the
    (anchor-widened) journey window, and the usable interval between arrival and
    departure must be non-empty.
    """

    if not anchors:
        return None
    windows = sorted(_anchor_windows(anchors), key=lambda item: (item[1], item[2]))
    for anchor, start_at, end_at in windows:
        if start_at < journey_start or end_at > journey_end:
            return (
                f"C4_ANCHOR_OUTSIDE_JOURNEY:{anchor.semantic_key}"
                f"@{start_at.isoformat()}"
            )
    for (first, _fs, first_end), (second, second_start, _se) in zip(windows, windows[1:]):
        if second_start < first_end:
            return (
                f"C4_ANCHOR_OVERLAP:{first.semantic_key}|{second.semantic_key}"
            )
    arrivals = [item for item in windows if item[0].role == ARRIVAL_ROLE]
    departures = [item for item in windows if item[0].role == DEPARTURE_ROLE]
    usable_start = max((item[2] for item in arrivals), default=journey_start)
    usable_end = min((item[1] for item in departures), default=journey_end)
    if usable_start > usable_end:
        arrival_key = arrivals[0][0].semantic_key if arrivals else "-"
        departure_key = departures[0][0].semantic_key if departures else "-"
        return (
            f"C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE:{arrival_key}"
            f"@{usable_start.isoformat()}|{departure_key}@{usable_end.isoformat()}"
        )
    return None


def usable_city_interval(
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
) -> tuple[datetime, datetime]:
    """The interval flexible city activity may occupy.

    Arrival completes the lower boundary; departure must be reached before the
    upper boundary.  With no anchors this is simply the journey window.
    """

    windows = _anchor_windows(anchors)
    arrivals = [item for item in windows if item[0].role == ARRIVAL_ROLE]
    departures = [item for item in windows if item[0].role == DEPARTURE_ROLE]
    usable_start = max((item[2] for item in arrivals), default=journey_start)
    usable_end = min((item[1] for item in departures), default=journey_end)
    return usable_start, usable_end


def _anchor_activity(anchor: ResolvedAnchor, start_at: datetime, end_at: datetime) -> CandidateActivity:
    return CandidateActivity(
        place_id=anchor.place_id,
        title=anchor.place.name,
        start_at=start_at,
        end_at=end_at,
        cost_minor=_place_cost(anchor.place),
        locked=True,
        anchor_role=anchor.role,
        metadata={
            "semantic_key": anchor.semantic_key,
            "anchor_role": anchor.role,
            "commitment_anchor": True,
        },
    )


def _optional_activities(
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
) -> list[CandidateActivity]:
    anchor_places = {anchor.place_id for anchor in anchors}
    optional: list[CandidateActivity] = []
    for place_id, title, start_text, end_text in template:
        if place_id not in places or place_id in anchor_places:
            continue
        place = places[place_id]
        optional.append(
            CandidateActivity(
                place_id=place_id,
                title=title,
                start_at=_template_start(journey_start, start_text),
                end_at=_template_start(journey_start, end_text),
                cost_minor=_place_cost(place),
                locked=place_id == "place-river-cruise",
            )
        )
    return optional


def schedule_template_with_anchors(
    *,
    journey: Journey,
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
    travel_minutes: Mapping[tuple[str, str], int] | None = None,
) -> list[CandidateActivity] | None:
    """Build one candidate schedule that respects the C4 temporal boundaries.

    ``ARRIVAL`` is a lower boundary and ``DEPARTURE`` an upper boundary for
    flexible city activity; ``MID_TRIP`` is an interior pinned commitment.
    Flexible POIs are packed into the gaps between anchors with real travel
    time, and are dropped when they do not fit rather than producing a plan
    that is temporally impossible.  Returns ``None`` when the anchors
    themselves are inconsistent.
    """

    if not anchors:
        schedule: list[CandidateActivity] = []
        for place_id, title, start_text, end_text in template:
            if place_id not in places:
                return None
            place = places[place_id]
            schedule.append(
                CandidateActivity(
                    place_id=place_id,
                    title=title,
                    start_at=_template_start(journey_start, start_text),
                    end_at=_template_start(journey_start, end_text),
                    cost_minor=_place_cost(place),
                    locked=place_id == "place-river-cruise",
                )
            )
        return schedule

    if validate_anchor_timeline(anchors, journey_start, journey_end) is not None:
        return None

    ordered_anchors = sorted(
        _anchor_windows(anchors), key=lambda item: (item[1], item[2])
    )
    usable_start, usable_end = usable_city_interval(
        anchors, journey_start, journey_end
    )
    if usable_start > usable_end:
        return None

    pending = _optional_activities(template, places, anchors, journey_start)
    schedule: list[CandidateActivity] = []
    cursor = usable_start
    previous_place: str | None = None
    next_index = 0

    while next_index < len(ordered_anchors):
        anchor, anchor_start, anchor_end = ordered_anchors[next_index]
        # Pack flexible POIs into the gap that ends at this anchor.
        while pending:
            candidate = pending[0]
            duration = candidate.end_at - candidate.start_at
            travel_in = _estimate_gap_minutes(
                travel_minutes, previous_place, candidate.place_id
            )
            start_at = max(
                candidate.start_at, cursor + timedelta(minutes=travel_in)
            )
            end_at = start_at + duration
            travel_out = _estimate_gap_minutes(
                travel_minutes, candidate.place_id, anchor.place_id
            )
            if end_at + timedelta(minutes=travel_out) > anchor_start:
                break
            schedule.append(
                CandidateActivity(
                    place_id=candidate.place_id,
                    title=candidate.title,
                    start_at=start_at,
                    end_at=end_at,
                    cost_minor=candidate.cost_minor,
                    locked=candidate.locked,
                    metadata=candidate.metadata,
                )
            )
            cursor = end_at
            previous_place = candidate.place_id
            pending.pop(0)
        # The anchor itself must still be reachable from the last POI.
        if previous_place is not None:
            needed = _estimate_gap_minutes(
                travel_minutes, previous_place, anchor.place_id
            )
            if cursor + timedelta(minutes=needed) > anchor_start:
                return None
        schedule.append(_anchor_activity(anchor, anchor_start, anchor_end))
        cursor = max(cursor, anchor_end)
        previous_place = anchor.place_id
        next_index += 1

    # Remaining POIs may only run up to the usable end (the DEPARTURE boundary).
    while pending:
        candidate = pending[0]
        duration = candidate.end_at - candidate.start_at
        travel_in = _estimate_gap_minutes(
            travel_minutes, previous_place, candidate.place_id
        )
        start_at = max(candidate.start_at, cursor + timedelta(minutes=travel_in))
        end_at = start_at + duration
        if end_at > usable_end:
            break
        schedule.append(
            CandidateActivity(
                place_id=candidate.place_id,
                title=candidate.title,
                start_at=start_at,
                end_at=end_at,
                cost_minor=candidate.cost_minor,
                locked=candidate.locked,
                metadata=candidate.metadata,
            )
        )
        cursor = end_at
        previous_place = candidate.place_id
        pending.pop(0)

    for item in schedule:
        if item.start_at < journey_start or item.end_at > journey_end:
            return None
        if item.anchor_role in (None, MID_TRIP_ROLE):
            if item.start_at < usable_start or item.end_at > usable_end:
                return None
    return schedule

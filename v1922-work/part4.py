

def schedule_template_with_anchors(
    *,
    journey: Journey,
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
) -> list[CandidateActivity] | None:
    """Return a candidate schedule, or ``None`` when the anchor cannot be met.

    Anchors are pinned to their exact required time.  Optional template POIs are
    re-timed around them; any POI that would overlap an anchor or leave the
    journey window is dropped instead of corrupting the plan.
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

    ordered = _merge_anchors(template, places, anchors, journey_start)
    if not ordered:
        return None
    schedule: list[CandidateActivity] = []
    cursor: datetime | None = None
    for item in ordered:
        if item.anchor_role is not None:
            # Drop any optional POI that cannot finish before the anchor starts.
            while schedule and cursor is not None and cursor > item.start_at:
                schedule.pop()
                cursor = schedule[-1].end_at if schedule else None
            if cursor is not None and cursor > item.start_at:
                return None
            schedule.append(item)
            cursor = item.end_at
            continue
        start_at = max(item.start_at, cursor) if cursor is not None else item.start_at
        duration = item.end_at - item.start_at
        end_at = start_at + duration
        if end_at > journey_end:
            # Cannot fit before the journey ends: drop this optional POI.
            continue
        schedule.append(
            CandidateActivity(
                place_id=item.place_id,
                title=item.title,
                start_at=start_at,
                end_at=end_at,
                cost_minor=item.cost_minor,
                locked=item.locked,
                anchor_role=None,
                metadata=item.metadata,
            )
        )
        cursor = end_at
    for item in schedule:
        if item.start_at < journey_start or item.end_at > journey_end:
            return None
    return schedule


def anchor_assignment_for_activities(
    activities: Sequence[Any],
    anchors: Sequence[ResolvedAnchor],
) -> dict[str, str]:
    """Map commitment semantic keys to the Activity ids that satisfy them."""

    assigned: dict[str, str] = {}
    for anchor in anchors:
        match = next(
            (
                item
                for item in activities
                if str(getattr(item, "place_id", None) or "") == anchor.place_id
            ),
            None,
        )
        if match is not None:
            assigned[anchor.semantic_key] = match.id
    return assigned

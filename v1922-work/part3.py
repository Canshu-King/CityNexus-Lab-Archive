

def _place_cost(place: Place) -> int:
    metadata = _load(place.metadata_json, {})
    try:
        return int(metadata.get("cost_minor", 0))
    except (TypeError, ValueError):
        return 0


def _place_duration(place: Place) -> int:
    metadata = _load(place.metadata_json, {})
    try:
        return max(15, int(metadata.get("duration_min", 60)))
    except (TypeError, ValueError):
        return 60


def _template_start(journey_start: datetime, text: str) -> datetime:
    hour, minute = (int(part) for part in str(text).split(":", 1))
    return journey_start.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _merge_anchors(
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
) -> list[CandidateActivity]:
    """Interleave anchors with template POIs in chronological order."""

    optional: list[CandidateActivity] = []
    for place_id, title, start_text, end_text in template:
        if place_id not in places:
            continue
        if any(place_id == anchor.place_id for anchor in anchors):
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
    anchor_rows: list[CandidateActivity] = []
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
        )
        if anchor.time_boundary == "END":
            start_at = anchor.scheduled_at - timedelta(minutes=duration)
            end_at = anchor.scheduled_at
        else:
            start_at = anchor.scheduled_at
            end_at = anchor.scheduled_at + timedelta(minutes=duration)
        anchor_rows.append(
            CandidateActivity(
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
        )
    return sorted(
        [*optional, *anchor_rows],
        key=lambda item: (item.start_at, 0 if item.anchor_role else 1, item.place_id),
    )

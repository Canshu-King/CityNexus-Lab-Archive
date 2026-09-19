"""Make the anchor scheduler travel-aware (insert real travel gaps)."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
s = P.read_text(encoding="utf-8")

old = '''    ordered = _merge_anchors(template, places, anchors, journey_start)
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
    return schedule'''

new = '''    ordered = _merge_anchors(template, places, anchors, journey_start)
    if not ordered:
        return None
    schedule: list[CandidateActivity] = []
    cursor: datetime | None = None
    previous_place: str | None = None
    for item in ordered:
        gap = (
            _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
            if previous_place
            else 0
        )
        if item.anchor_role is not None:
            # Drop optional POIs that would arrive late for the anchor.
            while schedule and cursor is not None and (
                cursor + timedelta(minutes=_estimate_gap_minutes(travel_minutes, previous_place, item.place_id))
                > item.start_at
            ):
                schedule.pop()
                cursor = schedule[-1].end_at if schedule else None
                previous_place = schedule[-1].place_id if schedule else None
            if cursor is not None:
                gap = _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
                if cursor + timedelta(minutes=gap) > item.start_at:
                    return None
            schedule.append(item)
            cursor = item.end_at
            previous_place = item.place_id
            continue
        start_at = max(item.start_at, cursor + timedelta(minutes=gap)) if cursor is not None else item.start_at
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
        previous_place = item.place_id
    for item in schedule:
        if item.start_at < journey_start or item.end_at > journey_end:
            return None
    return schedule'''

assert old in s, "scheduler body not found"
s = s.replace(old, new, 1)

old_sig = '''def schedule_template_with_anchors(
    *,
    journey: Journey,
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
) -> list[CandidateActivity] | None:'''
new_sig = '''def _estimate_gap_minutes(
    travel_minutes: Mapping[tuple[str, str], int] | None,
    origin: str | None,
    destination: str | None,
) -> int:
    """Frozen travel time for one leg, or the deterministic fixture default."""

    if not origin or not destination:
        return 0
    if travel_minutes is not None:
        value = travel_minutes.get((origin, destination))
        if value is not None:
            return int(value)
    return DEFAULT_TRAVEL_MIN


def schedule_template_with_anchors(
    *,
    journey: Journey,
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
    travel_minutes: Mapping[tuple[str, str], int] | None = None,
) -> list[CandidateActivity] | None:'''
assert old_sig in s
s = s.replace(old_sig, new_sig, 1)

s = s.replace(
    'ANCHOR_DURATION_MIN = 20',
    'ANCHOR_DURATION_MIN = 20\n# Deterministic fixture default when a pair is not frozen yet.\nDEFAULT_TRAVEL_MIN = 20',
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("scheduler patched")

from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")
old = '''    facts, rows = anchored
    total_cost = sum(int(cost) for *_rest, cost in [(r[4],) for r in rows])'''
new = '''    facts, rows = anchored
    total_cost = sum(int(row[4]) for row in rows)'''
assert old in s
s = s.replace(old, new, 1)

helpers = '''

def _inject_anchors_into_generic(
    *,
    journey: Journey,
    selected_ids: Sequence[str],
    places: Mapping[str, Any],
    anchors: Sequence[Any],
    facts: list[FeasibilityActivity],
    rows: list[Any],
) -> tuple[list[FeasibilityActivity], list[Any]] | None:
    """Insert resolved C4 anchors into an explicit-POI schedule.

    The optional POIs keep their relative order; anchors are pinned to their
    required time.  Returns ``None`` when an anchor cannot be satisfied.
    """

    if not anchors:
        return facts, rows
    # Rebuild the schedule from the (place, start, end, travel, cost) rows and
    # re-interleave the anchors, preserving the original POI ordering.
    scheduled: list[tuple[str, Any, Any, Any, int, str | None]] = []
    by_place = {place_id: row for row, place_id in zip(facts, selected_ids)}
    for place_id in selected_ids:
        fact = by_place.get(place_id)
        if fact is None:
            continue
        place = places.get(place_id)
        if place is None:
            return None
        scheduled.append(
            (place_id, fact.start_at, fact.end_at, fact.cost_minor, place.id, None)
        )
    anchor_rows = []
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, 60)
        )
        if anchor.time_boundary == "END":
            start_at = anchor.scheduled_at - timedelta(minutes=duration)
            end_at = anchor.scheduled_at
        else:
            start_at = anchor.scheduled_at
            end_at = anchor.scheduled_at + timedelta(minutes=duration)
        anchor_rows.append(
            (
                anchor.place_id,
                start_at,
                end_at,
                0,
                anchor.place_id,
                anchor.semantic_key,
                anchor.role,
            )
        )
    combined = [
        (
            item[0],
            item[1],
            item[2],
            item[3],
            item[4],
            item[5],
            None,
        )
        for item in scheduled
    ] + anchor_rows
    combined.sort(key=lambda item: (item[1], 0 if item[6] else 1, item[0]))
    new_facts: list[FeasibilityActivity] = []
    new_rows: list[Any] = []
    for place_id, start_at, end_at, cost_minor, db_place_id, semantic, role in combined:
        place = places.get(db_place_id) or places.get(place_id)
        if place is None:
            return None
        new_facts.append(
            FeasibilityActivity(
                key=place_id,
                place_id=db_place_id,
                start_at=start_at,
                end_at=end_at,
                cost_minor=int(cost_minor),
                currency=journey.budget_currency,
                travel_from_prev_min=0,
                locked=bool(role),
                metadata=(
                    {"semantic_key": semantic, "anchor_role": role, "commitment_anchor": True}
                    if role
                    else {"semantic_key": semantic or db_place_id}
                ),
            )
        )
        new_rows.append((place, start_at, end_at, 0, int(cost_minor)))
    return new_facts, new_rows
'''
marker = "\ndef validate_plan_feasibility("
assert marker in s
s = s.replace(marker, helpers + "\n\ndef validate_plan_feasibility(", 1)
s = s.replace(
    "from app.planning.anchor_schedule import (\n    CandidateActivity,\n    effective_journey_window,\n    resolve_plan_anchors,\n    schedule_template_with_anchors,\n)",
    "from app.planning.anchor_schedule import (\n    ANCHOR_DURATION_MIN,\n    CandidateActivity,\n    MID_TRIP_ROLE,\n    effective_journey_window,\n    resolve_plan_anchors,\n    schedule_template_with_anchors,\n)",
    1,
)
s = s.replace(
    "from app.planning.anchors import (\n    LOCATION_RESOLVED,\n    STRUCTURAL_ANCHOR_KEYS,\n    resolve_anchor_key,\n)",
    "from app.planning.anchors import (\n    LOCATION_RESOLVED,\n    STRUCTURAL_ANCHOR_KEYS,\n    resolve_anchor_key,\n)",
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")

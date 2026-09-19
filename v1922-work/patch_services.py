"""Apply the anchor-aware generation changes to app/services.py."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")


def sub(old, new, label):
    global s
    assert old in s, f"anchor not found: {label}"
    assert s.count(old) == 1, f"ambiguous anchor: {label}"
    s = s.replace(old, new, 1)


sub(
    """    constraints = _journey_constraints_with_capabilities(session, journey)
    raw_templates = _templates()
    created: list[PlanVersion] = []
    now = iso_now()
    journey_start = parse_dt(journey.start_at)""",
    """    constraints = _journey_constraints_with_capabilities(session, journey)
    raw_templates = _templates()
    created: list[PlanVersion] = []
    now = iso_now()
    journey_start = parse_dt(journey.start_at)
    journey_end = parse_dt(journey.end_at)
    # A confirmed C4 anchor is a requirement to *build around*, not only a veto.
    # Resolve every active anchor to a concrete, routable Place identity and pin
    # it into the candidate schedule before the gate runs.
    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)""",
    "anchor resolution",
)


sub(
    """    template_pairs = tuple(
        (template[index - 1][0], template[index][0])
        for template in raw_templates
        for index in range(1, len(template))
    )
    mobility_provider = capture_runtime_mobility_snapshot(""",
    """    schedules: list[list[CandidateActivity]] = []
    for template in raw_templates:
        schedule = schedule_template_with_anchors(
            journey=journey,
            template=template,
            places=places,
            anchors=anchors,
            journey_start=journey_start,
            journey_end=journey_end,
        )
        if schedule is not None:
            schedules.append(schedule)
    template_pairs = tuple(
        (template[index - 1][0], template[index][0])
        for template in raw_templates
        for index in range(1, len(template))
        if template[index - 1][0] in places and template[index][0] in places
    )
    schedule_pairs = tuple(
        (schedule[index - 1].place_id, schedule[index].place_id)
        for schedule in schedules
        for index in range(1, len(schedule))
    )
    mobility_provider = capture_runtime_mobility_snapshot(""",
    "mobility capture",
)


sub(
    """        template_pairs,
        operation_key=f"template-compose:{journey.id}",
    ).snapshot""",
    """        tuple(dict.fromkeys([*template_pairs, *schedule_pairs])),
        operation_key=f"template-compose:{journey.id}",
    ).snapshot""",
    "mobility pairs",
)


sub(
    """    for offset, template in enumerate(raw_templates):
        if len(created) >= candidate_count:
            break
        if any(place_id not in places for place_id, *_ in template):
            continue
        total_cost = sum(
            int(json.loads(places[p].metadata_json)["cost_minor"]) for p, *_ in template
        )
        if total_cost > journey.budget_amount_minor:
            continue""",
    """    for offset, schedule in enumerate(schedules):
        if len(created) >= candidate_count:
            break
        total_cost = sum(int(item.cost_minor) for item in schedule)
        if total_cost > journey.budget_amount_minor:
            continue""",
    "candidate loop head",
)


sub(
    """        for place_id, _, start, end in template:
            travel = (
                mobility_provider.estimate_minutes(previous_place, place_id)
                if previous_place
                else 0
            )
            activity_facts.append(
                FeasibilityActivity(
                    key=place_id,
                    place_id=place_id,
                    start_at=parse_dt(
                        f"{journey_start.date().isoformat()}T{start}:00{journey_start.strftime('%z')}"
                    ),
                    end_at=parse_dt(
                        f"{journey_start.date().isoformat()}T{end}:00{journey_start.strftime('%z')}"
                    ),
                    cost_minor=int(json.loads(places[place_id].metadata_json)["cost_minor"]),
                    currency=journey.budget_currency,
                    travel_from_prev_min=travel,
                    locked=(place_id == "place-river-cruise"),
                )
            )
            previous_place = place_id""",
    """        for item in schedule:
            travel = (
                _safe_estimate_minutes(mobility_provider, previous_place, item.place_id)
                if previous_place
                else 0
            )
            activity_facts.append(
                FeasibilityActivity(
                    key=item.place_id,
                    place_id=item.place_id,
                    start_at=item.start_at,
                    end_at=item.end_at,
                    cost_minor=item.cost_minor,
                    currency=journey.budget_currency,
                    travel_from_prev_min=travel,
                    locked=item.locked,
                    metadata=dict(item.metadata),
                )
            )
            previous_place = item.place_id""",
    "feasibility facts",
)


sub(
    """        for sequence, (place_id, title, start, end) in enumerate(template, start=1):
            aid = deterministic_id(f"activity:{plan_id}:{sequence}")
            travel = activity_facts[sequence - 1].travel_from_prev_min
            start_text = (
                f"{journey_start.date().isoformat()}T{start}:00{journey_start.strftime('%z')}"
            )
            end_text = f"{journey_start.date().isoformat()}T{end}:00{journey_start.strftime('%z')}"
            session.add(
                Activity(
                    id=aid,
                    plan_version_id=plan_id,
                    sequence_no=sequence,
                    activity_type="visit",
                    title=title,
                    place_id=place_id,
                    city_service_id=None,
                    start_at=start_text,
                    end_at=end_text,
                    travel_from_prev_min=travel,
                    estimated_cost_minor=int(
                        json.loads(places[place_id].metadata_json)["cost_minor"]
                    ),
                    currency=journey.budget_currency,
                    status="PLANNED",
                    locked=(place_id == "place-river-cruise"),
                    metadata_json=dump({}),
                    created_at=now,
                    updated_at=now,
                )
            )
        created.append(plan)""",
    """        for sequence, item in enumerate(schedule, start=1):
            aid = deterministic_id(f"activity:{plan_id}:{sequence}")
            travel = activity_facts[sequence - 1].travel_from_prev_min
            session.add(
                Activity(
                    id=aid,
                    plan_version_id=plan_id,
                    sequence_no=sequence,
                    activity_type=(
                        "arrival"
                        if item.anchor_role == "ARRIVAL"
                        else "departure"
                        if item.anchor_role == "DEPARTURE"
                        else "visit"
                    ),
                    title=item.title,
                    place_id=item.place_id,
                    city_service_id=None,
                    start_at=item.start_at.isoformat(),
                    end_at=item.end_at.isoformat(),
                    travel_from_prev_min=travel,
                    estimated_cost_minor=item.cost_minor,
                    currency=journey.budget_currency,
                    status="PLANNED",
                    locked=item.locked,
                    metadata_json=dump(dict(item.metadata)),
                    created_at=now,
                    updated_at=now,
                )
            )
        created.append(plan)""",
    "activity persistence",
)


sub(
    """    if not created:
        raise ValueError("No feasible plan candidates satisfy the journey constraints")""",
    """    if not created:
        if unresolved_anchors:
            raise ValueError(
                "C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved_anchors)))
            )
        detail = _anchor_block_reason(session, journey)
        raise ValueError(
            "No feasible plan candidates satisfy the journey constraints" + detail
        )""",
    "failure reason",
)


sub(
    """from app.replanning.protected_commitments import active_c4_hard_constraints""",
    """from app.planning.anchor_schedule import (
    CandidateActivity,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)
from app.replanning.protected_commitments import active_c4_hard_constraints""",
    "imports",
)

P.write_text(s, encoding="utf-8", newline="\n")
print("services.py patched")

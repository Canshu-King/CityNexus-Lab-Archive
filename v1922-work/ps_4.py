

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



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

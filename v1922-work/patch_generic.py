"""Make the explicit-POI compose path anchor-aware."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")

old = '''    constraints = _journey_constraints_with_capabilities(session, journey, active_only=True)
    services = {
        service.id: service
        for service in session.scalars(
            select(CityService).where(CityService.city_code == journey.city_code)
        ).all()
    }
    lookup = {
        item.id: {"location": {"latitude": item.latitude, "longitude": item.longitude}}
        for item in places.values()
    }'''
new = '''    constraints = _journey_constraints_with_capabilities(session, journey, active_only=True)
    # A confirmed C4 anchor is a requirement to build around on this path too.
    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)
    services = {
        service.id: service
        for service in session.scalars(
            select(CityService).where(CityService.city_code == journey.city_code)
        ).all()
    }
    lookup = {
        item.id: {"location": {"latitude": item.latitude, "longitude": item.longitude}}
        for item in places.values()
    }'''
assert old in s, "generic constraints block not found"
s = s.replace(old, new, 1)

old2 = '''    mobility_pairs = tuple(
        (origin, destination)
        for origin in selected_ids
        for destination in selected_ids
        if origin != destination
    )'''
new2 = '''    schedulable_ids = tuple(dict.fromkeys([*selected_ids, *(a.place_id for a in anchors)]))
    mobility_pairs = tuple(
        (origin, destination)
        for origin in schedulable_ids
        for destination in schedulable_ids
        if origin != destination
    )'''
assert old2 in s, "mobility pairs not found"
s = s.replace(old2, new2, 1)

old3 = '''    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=mobility_provider,
        ),
        facts,
    )
    if not gate.passed:
        raise ValueError(f"GENERIC_COMPOSE_INFEASIBLE:{'|'.join(gate.failures)}")'''
new3 = '''    # Pin every resolved anchor into the candidate schedule before the gate.
    anchored = _inject_anchors_into_generic(
        journey=journey,
        selected_ids=ordered_ids,
        places=places,
        anchors=anchors,
        facts=facts,
        rows=rows,
    )
    if anchored is None:
        if unresolved_anchors:
            raise ValueError(
                "C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved_anchors)))
            )
        raise ValueError("GENERIC_COMPOSE_INFEASIBLE:C4_ANCHOR_UNSATISFIABLE")
    facts, rows = anchored
    total_cost = sum(int(cost) for *_rest, cost in [(r[4],) for r in rows])
    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=mobility_provider,
        ),
        facts,
    )
    if not gate.passed:
        raise ValueError(f"GENERIC_COMPOSE_INFEASIBLE:{'|'.join(gate.failures)}")'''
assert old3 in s, "generic gate block not found"
s = s.replace(old3, new3, 1)

old4 = '''                metadata_json=dump(
                    {
                        "compose_source": "EXPLICIT_POI_SET",
                        "category": place.category,
                        "opening_hours": json.loads(place.opening_hours_json or "{}"),
                    }
                ),'''
new4 = '''                metadata_json=dump(
                    {
                        "compose_source": "EXPLICIT_POI_SET",
                        "semantic_key": (
                            f"v12:{journey.id}:{place.category.upper()}-anchor"
                            if place.category.upper() in {"ARRIVAL", "DEPARTURE"}
                            else place.id
                        ),
                        "category": place.category,
                        "opening_hours": json.loads(place.opening_hours_json or "{}"),
                    }
                ),'''
assert old4 in s, "generic metadata not found"
s = s.replace(old4, new4, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("generic compose patched")

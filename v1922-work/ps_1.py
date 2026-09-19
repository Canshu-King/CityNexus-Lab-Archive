

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



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

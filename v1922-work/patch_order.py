"""Capture mobility before scheduling so the scheduler can use real travel times."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")

old = '''    schedules: list[list[CandidateActivity]] = []
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
    mobility_provider = capture_runtime_mobility_snapshot(
        session,
        journey,
        tuple(dict.fromkeys([*template_pairs, *schedule_pairs])),
        operation_key=f"template-compose:{journey.id}",
    ).snapshot'''

new = '''    # Capture one frozen mobility matrix over every node a candidate can visit
    # (template POIs plus resolved anchors) *before* scheduling, so the
    # scheduler inserts real travel gaps and the gate consumes the exact same
    # frozen evidence.
    schedulable_ids = tuple(
        dict.fromkeys(
            [
                *(
                    place_id
                    for template in raw_templates
                    for place_id, *_ in template
                    if place_id in places
                ),
                *(anchor.place_id for anchor in anchors),
            ]
        )
    )
    mobility_provider = capture_runtime_mobility_snapshot(
        session,
        journey,
        tuple(
            (origin, destination)
            for origin in schedulable_ids
            for destination in schedulable_ids
            if origin != destination
        ),
        operation_key=f"template-compose:{journey.id}",
    ).snapshot
    travel_minutes = {
        (origin, destination): fact.minutes
        for (origin, destination), fact in mobility_provider.facts.items()
    }
    schedules: list[list[CandidateActivity]] = []
    for template in raw_templates:
        schedule = schedule_template_with_anchors(
            journey=journey,
            template=template,
            places=places,
            anchors=anchors,
            journey_start=journey_start,
            journey_end=journey_end,
            travel_minutes=travel_minutes,
        )
        if schedule is not None:
            schedules.append(schedule)'''

assert old in s, "order block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")

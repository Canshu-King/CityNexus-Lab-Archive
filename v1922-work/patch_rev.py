"""Let the gate own window widening; drop the services-side override."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")

old = '''    overrides = dict(journey_overrides or {})
    # The effective window must contain every confirmed C4 anchor, exactly as
    # generation did.  Recomputing it here (instead of trusting the draft
    # window) is what keeps generate / select / booking / start in agreement.
    anchor_start: str | None = None
    anchor_end: str | None = None
    if include_active_c4:
        try:
            anchors, _unresolved = resolve_plan_anchors(session, journey)
        except Exception:  # noqa: BLE001 - never break validation on anchor read
            anchors = []
        if anchors:
            anchor_start, anchor_end = effective_journey_window(journey, anchors)
    proposed_journey = {
        "id": journey.id,
        "city_code": overrides.get("city_code", journey.city_code),
        "start_at": overrides.get("start_at")
        or overrides.get("effective_start_at")
        or anchor_start
        or journey.start_at,
        "end_at": overrides.get("end_at")
        or overrides.get("effective_end_at")
        or anchor_end
        or journey.end_at,
        "budget_amount_minor": overrides.get("budget_amount_minor", journey.budget_amount_minor),
        "budget_currency": overrides.get("budget_currency", journey.budget_currency),
    }'''

new = '''    overrides = dict(journey_overrides or {})
    # The effective journey window is widened inside ``evaluate_feasibility``
    # from the active C4 constraints themselves, so generation and every
    # revalidation (select / booking / start) automatically agree.
    proposed_journey = {
        "id": journey.id,
        "city_code": overrides.get("city_code", journey.city_code),
        "start_at": overrides.get("start_at", journey.start_at),
        "end_at": overrides.get("end_at", journey.end_at),
        "budget_amount_minor": overrides.get("budget_amount_minor", journey.budget_amount_minor),
        "budget_currency": overrides.get("budget_currency", journey.budget_currency),
    }'''

assert old in s, "revalidation override not found"
s = s.replace(old, new, 1)
s = s.replace(
    '''from app.planning.anchor_schedule import (
    CandidateActivity,
    effective_journey_window,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)''',
    '''from app.planning.anchor_schedule import (
    CandidateActivity,
    effective_journey_window,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)''',
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")

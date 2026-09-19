"""Use the anchor-widened effective window in generation and revalidation."""

from pathlib import Path

# --- services.py: generation uses the widened window ------------------------
P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")

old = '''    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)'''
new = '''    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)
    # A confirmed reservation is an authoritative real-world fact: the draft
    # journey window expands to contain it rather than making it unplannable.
    effective_start_text, effective_end_text = effective_journey_window(
        journey, anchors
    )
    journey_start = parse_dt(effective_start_text)
    journey_end = parse_dt(effective_end_text)'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''from app.planning.anchor_schedule import (
    CandidateActivity,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)'''
new2 = '''from app.planning.anchor_schedule import (
    CandidateActivity,
    effective_journey_window,
    resolve_plan_anchors,
    schedule_template_with_anchors,
)'''
assert old2 in s
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")

# --- services.py: revalidation uses the same widened window -----------------
old3 = '''    overrides = dict(journey_overrides or {})
    proposed_journey = {
        "id": journey.id,
        "city_code": overrides.get("city_code", journey.city_code),
        "start_at": overrides.get("start_at", journey.start_at),
        "end_at": overrides.get("end_at", journey.end_at),
        "budget_amount_minor": overrides.get("budget_amount_minor", journey.budget_amount_minor),
        "budget_currency": overrides.get("budget_currency", journey.budget_currency),
    }'''
new3 = '''    overrides = dict(journey_overrides or {})
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
assert old3 in s, "revalidation window not found"
s = s.replace(old3, new3, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("windows patched")

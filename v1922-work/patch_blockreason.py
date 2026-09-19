from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/services.py")
s = p.read_text(encoding="utf-8")

old = '''    try:
        anchors, unresolved = resolve_plan_anchors(session, journey)
    except Exception:  # noqa: BLE001 - reason text must never break generation
        return ""
    if unresolved:
        return ": C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved)))
    if anchors:
        keys = ", ".join(sorted({anchor.semantic_key for anchor in anchors}))
        return f": C4_ANCHOR_BLOCKED:{keys}"
    return ""'''

new = '''    try:
        anchors, unresolved = resolve_plan_anchors(session, journey)
    except Exception:  # noqa: BLE001 - reason text must never break generation
        return ""
    if unresolved:
        return ": C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved)))
    if not anchors:
        return ""
    # Prefer the precise structural reason (overlap, arrival-after-departure,
    # outside journey) over a generic "blocked" list.
    try:
        effective_start, effective_end = effective_journey_window(journey, anchors)
        conflict = validate_anchor_timeline(
            anchors,
            parse_dt(effective_start),
            parse_dt(effective_end),
        )
    except Exception:  # noqa: BLE001
        conflict = None
    if conflict:
        return f": {conflict}"
    keys = ", ".join(sorted({anchor.semantic_key for anchor in anchors}))
    return f": C4_ANCHOR_BLOCKED:{keys}"'''
assert old in s, "block reason not found"
s = s.replace(old, new, 1)
s = s.replace(
    "from app.planning.anchor_schedule import (\n    ANCHOR_DURATION_MIN,\n    CandidateActivity,\n    MID_TRIP_ROLE,\n    effective_journey_window,\n    resolve_plan_anchors,\n    schedule_template_with_anchors,\n)",
    "from app.planning.anchor_schedule import (\n    ANCHOR_DURATION_MIN,\n    CandidateActivity,\n    MID_TRIP_ROLE,\n    effective_journey_window,\n    resolve_plan_anchors,\n    schedule_template_with_anchors,\n    validate_anchor_timeline,\n)",
    1,
)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("ok")

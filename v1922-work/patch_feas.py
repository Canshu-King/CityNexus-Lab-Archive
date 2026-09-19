"""Widen the effective journey window to contain active C4 anchors (gate-side)."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = P.read_text(encoding="utf-8")

old = '''    hard_constraints = _active_hard_constraints(context)
    effective_start = context.journey_start
    effective_end = context.journey_end
    budget_max = context.budget_amount_minor'''

new = '''    hard_constraints = _active_hard_constraints(context)
    effective_start = context.journey_start
    effective_end = context.journey_end
    budget_max = context.budget_amount_minor
    # A confirmed reservation is an authoritative real-world fact.  The draft
    # journey window must contain it, otherwise generate and revalidation would
    # disagree about the same commitment.
    for _kind, _category, code, params in hard_constraints:
        if code != "LOCKED_COMMITMENT":
            continue
        raw_start = params.get("start_at") or params.get("time")
        if raw_start is None:
            continue
        try:
            anchor_at = _parse_dt(raw_start, reference=context.journey_start)
        except (TypeError, ValueError):
            continue
        boundary = str(params.get("time_boundary") or "START").upper()
        if boundary == "END":
            anchor_start = anchor_at - timedelta(minutes=_ANCHOR_DURATION_MIN)
            anchor_end = anchor_at
        else:
            anchor_start = anchor_at
            anchor_end = anchor_at + timedelta(minutes=_ANCHOR_DURATION_MIN)
        effective_start = min(effective_start, anchor_start)
        effective_end = max(effective_end, anchor_end)'''

assert old in s, "gate window anchor not found"
s = s.replace(old, new, 1)

s = s.replace(
    '''_CAPABILITY_GATE_CODES = {''',
    '''# A structural C4 anchor occupies a bounded slot; this mirrors
# ``app.planning.anchor_schedule.ANCHOR_DURATION_MIN`` so both sides agree.
_ANCHOR_DURATION_MIN = 20

_CAPABILITY_GATE_CODES = {''',
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("feasibility patched")

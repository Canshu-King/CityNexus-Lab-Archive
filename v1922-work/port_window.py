from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = p.read_text(encoding="utf-8")

# 1) 恢复"锚点是权威事实"的窗口加宽，但它只用于容纳锚点本身，
#    绝不用于放宽弹性活动的时间边界。
old = '''    effective_start = context.journey_start
    effective_end = context.journey_end
    budget_max = context.budget_amount_minor
    # C4 anchors are authoritative facts inside the Journey window.  Never
    # widen the Journey window to make an impossible reservation appear valid:
    # ARRIVAL and DEPARTURE are structural boundaries for flexible city
    # activity, while MID_TRIP remains an interior pinned commitment.'''

new = '''    effective_start = context.journey_start
    effective_end = context.journey_end
    budget_max = context.budget_amount_minor
    # A confirmed reservation is an authoritative real-world fact: the draft
    # Journey window must contain it (a booked 08:00 departure cannot be made
    # unplannable by a 09:00 draft start).  This widening applies only to the
    # *anchor* window checks below - it never relaxes the ARRIVAL/DEPARTURE
    # boundaries that constrain flexible city activity.
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
assert old in s, "window block not found"
s = s.replace(old, new, 1)

# 2) 锚点"越界"判定改为相对有效窗口（锚点加宽后的窗口），
#    这样 08:00 离城在 09:00 草稿行程中不再被误判。
old2 = '''    anchor_keys = {commitment.activity_key for commitment, _role in locked_specs}
    arrival_end_min: int | None = None
    departure_start_min: int | None = None
    journey_span_min = _minutes_from_start(context.journey_end, context.journey_start)'''
new2 = '''    anchor_keys = {commitment.activity_key for commitment, _role in locked_specs}
    arrival_end_min: int | None = None
    departure_start_min: int | None = None
    # An anchor is only "outside the Journey" relative to the anchor-widened
    # window, otherwise a reservation that legitimately defines the trip edges
    # (for example an 08:00 departure on a 09:00 draft) would be rejected.
    effective_span_min = _minutes_from_start(effective_end, effective_start)'''
assert old2 in s, "anchor span block not found"
s = s.replace(old2, new2, 1)

old3 = '''        if anchor_start_min < 0 or anchor_end_min > journey_span_min:
            failures.append(f"C4_ANCHOR_OUTSIDE_JOURNEY:{commitment.activity_key}")'''
new3 = '''        anchor_start_rel = anchor_start_min - _minutes_from_start(
            effective_start, context.journey_start
        )
        anchor_end_rel = anchor_end_min - _minutes_from_start(
            effective_start, context.journey_start
        )
        if anchor_start_rel < 0 or anchor_end_rel > effective_span_min:
            failures.append(f"C4_ANCHOR_OUTSIDE_JOURNEY:{commitment.activity_key}")'''
assert old3 in s, "outside journey block not found"
s = s.replace(old3, new3, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("窗口语义已移植")

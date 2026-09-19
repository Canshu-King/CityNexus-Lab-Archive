"""Snapshot M truth-edge probe.

Run from the authoritative backend environment.

This probe is intentionally small. Snapshot L is expected to fail the scheduler
cases before the fixes.
"""
from datetime import datetime, timedelta

import app.stay_mobility as sm
from app.stay_mobility import GraphNode, StayItineraryConflict, _reschedule_with_carried

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)

def node(key, role, start, end, *, locked=False, lat=24.50, lon=118.10):
    return GraphNode(
        key=key,
        title=key,
        role=role,
        start_at=start,
        end_at=end,
        latitude=lat,
        longitude=lon,
        place_key=key,
        locked=locked,
    )

def case_no_silent_duration_shrink():
    arrival = dt("2026-11-06T10:00:00+08:00")
    departure = dt("2026-11-06T16:00:00+08:00")
    anchors = [
        node("arrival", "ARRIVAL",
             "2026-11-06T10:00:00+08:00", "2026-11-06T10:20:00+08:00", locked=True),
        node("checkin", "CHECK_IN",
             "2026-11-06T11:30:00+08:00", "2026-11-06T11:50:00+08:00", locked=True),
        node("departure", "DEPARTURE",
             "2026-11-06T15:50:00+08:00", "2026-11-06T16:00:00+08:00", locked=True),
    ]
    carried = [
        node("museum", "ACTIVITY",
             "2026-11-06T10:30:00+08:00", "2026-11-06T12:30:00+08:00")
    ]

    # Keep transition cost deterministic and small enough that a truncated
    # 15-40 minute visit could fit, but the original 120 minutes cannot.
    old = sm._travel_minutes
    sm._travel_minutes = lambda a, b, journey=None: 5
    try:
        try:
            out = _reschedule_with_carried(anchors, carried, arrival, departure, journey=None)
        except StayItineraryConflict:
            return
    finally:
        sm._travel_minutes = old

    museum = next(x for x in out if x.key == "museum")
    actual = dt(museum.end_at) - dt(museum.start_at)
    original = timedelta(hours=2)
    assert actual == original, (
        f"hotel selection silently shortened activity from {original} to {actual}"
    )

def case_pinned_pair_requires_travel():
    arrival = dt("2026-11-06T10:00:00+08:00")
    departure = dt("2026-11-06T16:00:00+08:00")
    anchors = [
        node("arrival", "ARRIVAL",
             "2026-11-06T10:00:00+08:00", "2026-11-06T10:20:00+08:00", locked=True),
        node("checkin", "CHECK_IN",
             "2026-11-06T12:00:00+08:00", "2026-11-06T12:20:00+08:00",
             locked=True, lat=24.50, lon=118.10),
        node("departure", "DEPARTURE",
             "2026-11-06T15:50:00+08:00", "2026-11-06T16:00:00+08:00", locked=True),
    ]
    carried = [
        node("confirmed", "ACTIVITY",
             "2026-11-06T12:30:00+08:00", "2026-11-06T13:30:00+08:00",
             locked=True, lat=24.70, lon=118.30)
    ]

    old = sm._travel_minutes
    sm._travel_minutes = lambda a, b, journey=None: 30
    try:
        try:
            _reschedule_with_carried(anchors, carried, arrival, departure, journey=None)
        except StayItineraryConflict:
            return
    finally:
        sm._travel_minutes = old

    raise AssertionError(
        "pinned nodes were accepted despite only 10 minutes gap for 30 minutes travel"
    )

if __name__ == "__main__":
    cases = [
        case_no_silent_duration_shrink,
        case_pinned_pair_requires_travel,
    ]
    failed = 0
    for case in cases:
        try:
            case()
            print("PASS", case.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", case.__name__, "=>", exc)
    raise SystemExit(1 if failed else 0)

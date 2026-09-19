"""Snapshot L edge probe for the stay calendar.

Run from the authoritative backend environment:

    python snapshot_l_scheduler_edges.py

Snapshot K is expected to fail at least these new edge cases.
"""
from __future__ import annotations
from datetime import datetime, timedelta

import app.stay_mobility as sm
from app.stay_mobility import GraphNode, StayItineraryConflict, _reschedule_with_carried

TZ = "+08:00"

def dt(v: str) -> datetime:
    return datetime.fromisoformat(v)

def node(key, role, start, end, *, locked=False):
    return GraphNode(
        key=key, title=key, role=role,
        start_at=start, end_at=end,
        latitude=24.5, longitude=118.1,
        place_key=key, locked=locked,
    )

def local_date(n: GraphNode):
    return dt(n.start_at).date()

# Deterministic transition time so the contract is easy to inspect.
sm._travel_minutes = lambda a, b, journey=None: 30 if a is not None else 30

def case_inbound_outbound_pinned_travel():
    arrival = dt(f"2026-11-06T10:00:00{TZ}")
    departure = dt(f"2026-11-06T15:00:00{TZ}")
    anchors = [
        node("arrival", "ARRIVAL", arrival.isoformat(), "2026-11-06T10:20:00+08:00", locked=True),
        node("locked", "ACTIVITY", "2026-11-06T12:00:00+08:00", "2026-11-06T13:00:00+08:00", locked=True),
        node("departure", "DEPARTURE", "2026-11-06T14:50:00+08:00", departure.isoformat(), locked=True),
    ]
    carried = [
        node("flex", "ACTIVITY", "2026-11-06T10:30:00+08:00", "2026-11-06T11:30:00+08:00"),
        node("locked", "ACTIVITY", "2026-11-06T12:00:00+08:00", "2026-11-06T13:00:00+08:00", locked=True),
    ]
    out = _reschedule_with_carried(anchors, carried, arrival, departure, journey=None)
    flex = next(n for n in out if n.key == "flex")
    assert dt(flex.start_at) >= dt("2026-11-06T10:50:00+08:00"), (
        "first flexible stop did not reserve travel from ARRIVAL"
    )
    assert dt(flex.end_at) + timedelta(minutes=30) <= dt("2026-11-06T12:00:00+08:00"), (
        "flexible stop did not leave travel time to the next locked boundary"
    )

def case_pinned_overlap_rejected():
    arrival = dt(f"2026-11-06T10:00:00{TZ}")
    departure = dt(f"2026-11-06T16:00:00{TZ}")
    anchors = [
        node("arrival", "ARRIVAL", arrival.isoformat(), "2026-11-06T10:20:00+08:00", locked=True),
        node("checkin", "CHECK_IN", "2026-11-06T12:00:00+08:00", "2026-11-06T12:30:00+08:00", locked=True),
        node("departure", "DEPARTURE", "2026-11-06T15:50:00+08:00", departure.isoformat(), locked=True),
    ]
    carried = [
        node("confirmed", "ACTIVITY", "2026-11-06T12:15:00+08:00", "2026-11-06T13:00:00+08:00", locked=True),
    ]
    try:
        _reschedule_with_carried(anchors, carried, arrival, departure, journey=None)
    except StayItineraryConflict:
        return
    raise AssertionError("overlapping pinned CHECK_IN and locked activity were emitted")

def case_no_silent_cross_day_compaction():
    arrival = dt(f"2026-11-06T09:00:00{TZ}")
    departure = dt(f"2026-11-08T20:00:00{TZ}")
    anchors = [
        node("arrival", "ARRIVAL", arrival.isoformat(), "2026-11-06T09:20:00+08:00", locked=True),
        node("checkin", "CHECK_IN", "2026-11-06T18:00:00+08:00", "2026-11-06T18:20:00+08:00", locked=True),
        node("night1", "STAY", "2026-11-06T22:30:00+08:00", "2026-11-07T06:30:00+08:00", locked=True),
        node("night2", "STAY", "2026-11-07T22:30:00+08:00", "2026-11-08T06:30:00+08:00", locked=True),
        node("checkout", "CHECK_OUT", "2026-11-08T12:00:00+08:00", "2026-11-08T12:20:00+08:00", locked=True),
        node("departure", "DEPARTURE", "2026-11-08T19:50:00+08:00", departure.isoformat(), locked=True),
    ]
    carried = [
        node("day1", "ACTIVITY", "2026-11-06T11:00:00+08:00", "2026-11-06T12:00:00+08:00"),
        node("day2", "ACTIVITY", "2026-11-07T10:00:00+08:00", "2026-11-07T11:00:00+08:00"),
        node("day3", "ACTIVITY", "2026-11-08T09:00:00+08:00", "2026-11-08T10:00:00+08:00"),
    ]
    out = _reschedule_with_carried(anchors, carried, arrival, departure, journey=None)
    by_key = {n.key: n for n in out}
    assert local_date(by_key["day1"]) == dt("2026-11-06T11:00:00+08:00").date()
    assert local_date(by_key["day2"]) == dt("2026-11-07T10:00:00+08:00").date(), (
        "Day-2 activity was silently moved to another day by hotel selection"
    )
    assert local_date(by_key["day3"]) == dt("2026-11-08T09:00:00+08:00").date(), (
        "Day-3 activity was silently moved to another day by hotel selection"
    )

if __name__ == "__main__":
    cases = [
        case_inbound_outbound_pinned_travel,
        case_pinned_overlap_rejected,
        case_no_silent_cross_day_compaction,
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

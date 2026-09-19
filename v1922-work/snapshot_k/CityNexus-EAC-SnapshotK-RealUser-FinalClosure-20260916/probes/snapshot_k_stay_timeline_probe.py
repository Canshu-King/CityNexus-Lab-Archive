"""Snapshot K stay-timeline regression probe.

Run from the authoritative backend environment:

    python <this_file>

The probe imports the real scheduling function. Current Snapshot K candidate is
expected to FAIL at least the first two cases before the fix.
"""
from datetime import datetime, timedelta
from app.stay_mobility import GraphNode, _reschedule_with_carried

def dt(value: str):
    return datetime.fromisoformat(value)

def node(key, role, start, end, *, lat=24.50, lon=118.10, locked=False):
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

def overlap(a, b):
    return not (
        dt(a.end_at) <= dt(b.start_at)
        or dt(a.start_at) >= dt(b.end_at)
    )

def case_multiday_checkin():
    arrival_at = dt("2026-11-06T10:00:00+08:00")
    departure_at = dt("2026-11-08T20:00:00+08:00")
    anchors = [
        node("arrival","ARRIVAL",arrival_at.isoformat(),(arrival_at+timedelta(minutes=20)).isoformat(),locked=True),
        node("checkin","CHECK_IN","2026-11-06T14:00:00+08:00","2026-11-06T14:20:00+08:00",locked=True),
        node("night1","STAY","2026-11-06T22:30:00+08:00","2026-11-07T06:30:00+08:00",locked=True),
        node("night2","STAY","2026-11-07T22:30:00+08:00","2026-11-08T06:30:00+08:00",locked=True),
        node("checkout","CHECK_OUT","2026-11-08T12:00:00+08:00","2026-11-08T12:20:00+08:00",locked=True),
        node("departure","DEPARTURE","2026-11-08T19:50:00+08:00",departure_at.isoformat(),locked=True),
    ]
    original = [
        "2026-11-06T11:00:00+08:00","2026-11-06T15:30:00+08:00",
        "2026-11-06T17:00:00+08:00","2026-11-07T10:00:00+08:00",
        "2026-11-07T13:00:00+08:00","2026-11-07T16:00:00+08:00",
        "2026-11-08T09:00:00+08:00","2026-11-08T13:00:00+08:00",
    ]
    carried=[]
    for i, start in enumerate(original):
        s=dt(start)
        carried.append(node(f"p{i+1}","ACTIVITY",s.isoformat(),(s+timedelta(hours=1)).isoformat(),lat=24.49+i*.005,lon=118.12+i*.005))
    out=_reschedule_with_carried(anchors,carried,arrival_at,departure_at,journey=None)
    checkin=next(x for x in out if x.role=="CHECK_IN")
    first_stay=min((x for x in out if x.role=="STAY"),key=lambda x:dt(x.start_at))
    assert dt(checkin.end_at) <= dt(first_stay.start_at), (
        f"CHECK_IN occurs after first STAY: {checkin.start_at} vs {first_stay.start_at}"
    )

def case_flexible_locked_overlap():
    arrival_at=dt("2026-11-06T10:00:00+08:00")
    departure_at=dt("2026-11-06T20:00:00+08:00")
    anchors=[
        node("arrival","ARRIVAL",arrival_at.isoformat(),(arrival_at+timedelta(minutes=20)).isoformat(),locked=True),
        node("checkin","CHECK_IN","2026-11-06T16:00:00+08:00","2026-11-06T16:20:00+08:00",locked=True),
        node("departure","DEPARTURE","2026-11-06T19:50:00+08:00",departure_at.isoformat(),locked=True),
    ]
    carried=[
        node("flex","ACTIVITY","2026-11-06T11:00:00+08:00","2026-11-06T13:00:00+08:00"),
        node("locked","ACTIVITY","2026-11-06T12:00:00+08:00","2026-11-06T13:00:00+08:00",locked=True),
    ]
    out=_reschedule_with_carried(anchors,carried,arrival_at,departure_at,journey=None)
    flex=next(x for x in out if x.key=="flex")
    locked=next(x for x in out if x.key=="locked")
    assert not overlap(flex,locked), (
        f"flexible activity overlaps locked truth: {flex.start_at}-{flex.end_at} "
        f"vs {locked.start_at}-{locked.end_at}"
    )

if __name__ == "__main__":
    cases=[case_multiday_checkin,case_flexible_locked_overlap]
    failed=0
    for case in cases:
        try:
            case()
            print("PASS", case.__name__)
        except Exception as exc:
            failed+=1
            print("FAIL", case.__name__, "=>", exc)
    raise SystemExit(1 if failed else 0)

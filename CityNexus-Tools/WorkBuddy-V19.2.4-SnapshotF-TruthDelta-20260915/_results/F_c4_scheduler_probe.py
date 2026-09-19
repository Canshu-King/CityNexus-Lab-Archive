"""T01-T05: direct execution of Snapshot E's schedule_template_with_anchors().

Independent delta gate. Reads only the frozen lab tree. No DB, no server.
Asserts ACTUAL activity timestamps, never "a plan exists".
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("CITYNEXUS_TREE") or os.path.join(LAB, "_tree", "backend")
sys.path.insert(0, TREE)

from app.planning.anchor_schedule import (  # noqa: E402
    CandidateActivity,
    ResolvedAnchor,
    effective_journey_window,
    schedule_template_with_anchors,
)
from app.planning.anchors import (  # noqa: E402
    ARRIVAL_ROLE,
    DEPARTURE_ROLE,
    MID_TRIP_ROLE,
)

TZ = datetime.now().astimezone().tzinfo


class StubPlace:
    def __init__(self, pid: str, name: str, duration_min: int = 60, cost_minor: int = 0):
        self.id = pid
        self.name = name
        self.metadata_json = json.dumps(
            {"duration_min": duration_min, "cost_minor": cost_minor, "available": True}
        )


class StubJourney:
    def __init__(self, start: str, end: str):
        self.id = "J-C4-DELTA"
        self.city_code = "CITY-DELTA"
        self.start_at = start
        self.end_at = end
        self.budget_amount_minor = 10_000_00
        self.budget_currency = "EUR"


# The authoritative production templates (app/services.py::_templates()).
TEMPLATE = [
    ("place-old-town", "Old Town Gate", "09:00", "10:15"),
    ("place-riverside-museum", "Riverside Museum", "10:30", "11:45"),
    ("place-food-hall", "Central Food Hall", "12:00", "13:00"),
    ("place-city-park", "Nexus City Park", "13:20", "14:20"),
    ("place-river-cruise", "Nexus River Cruise Pier", "15:30", "16:30"),
    ("place-skyline-dinner", "Skyline Dinner House", "17:00", "18:30"),
]

PLACES = {pid: StubPlace(pid, title) for pid, title, _s, _e in TEMPLATE}


def anchor(role: str, at: str, start: datetime) -> ResolvedAnchor:
    hh, mm = (int(p) for p in at.split(":"))
    when = start.replace(hour=hh, minute=mm, second=0, microsecond=0)
    pid = f"v12:J-C4-DELTA:{role.lower()}-anchor"
    place = StubPlace(pid, "Arrival" if role == ARRIVAL_ROLE else "Departure")
    return ResolvedAnchor(
        role=role,
        semantic_key=pid,
        place_id=pid,
        place=place,
        scheduled_at=when,
        time_boundary="END" if role == DEPARTURE_ROLE else "START",
    )


def mid_anchor(at: str, start: datetime, pid: str = "place-riverside-museum") -> ResolvedAnchor:
    hh, mm = (int(p) for p in at.split(":"))
    when = start.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return ResolvedAnchor(
        role=MID_TRIP_ROLE,
        semantic_key=pid,
        place_id=pid,
        place=PLACES[pid],
        scheduled_at=when,
        time_boundary="START",
    )


def fmt(items):
    return [
        {
            "title": i.title,
            "place_id": i.place_id,
            "start": i.start_at.strftime("%H:%M"),
            "end": i.end_at.strftime("%H:%M"),
            "anchor_role": i.anchor_role,
            "locked": i.locked,
        }
        for i in items
    ]


def run(name: str, journey_start_text: str, journey_end_text: str, anchors):
    js = datetime.fromisoformat(journey_start_text).replace(tzinfo=TZ)
    je = datetime.fromisoformat(journey_end_text).replace(tzinfo=TZ)
    js_text = js.isoformat()
    je_text = je.isoformat()
    resolved = [a(js) if callable(a) else a for a in anchors]
    places = dict(PLACES)
    for a in resolved:
        places.setdefault(a.place_id, a.place)
    eff_start, eff_end = effective_journey_window(
        StubJourney(js_text, je_text), resolved
    )
    sched = schedule_template_with_anchors(
        journey=StubJourney(js_text, je_text),
        template=TEMPLATE,
        places=places,
        anchors=resolved,
        journey_start=datetime.fromisoformat(eff_start),
        journey_end=datetime.fromisoformat(eff_end),
        travel_minutes=None,  # deterministic DEFAULT_TRAVEL_MIN = 20
    )
    out = {
        "case": name,
        "journey_window": [journey_start_text, journey_end_text],
        "effective_window": [eff_start, eff_end],
        "anchors": [
            {
                "role": a.role,
                "boundary": a.time_boundary,
                "scheduled_at": a.scheduled_at.strftime("%H:%M"),
            }
            for a in resolved
        ],
        "schedule": None if sched is None else fmt(sched),
    }
    return out, sched, resolved


def boundary_violations(sched, resolved, journey_start: datetime, journey_end: datetime):
    """Return the list of temporal-boundary violations in a produced schedule."""
    problems = []
    arrival = next((a for a in resolved if a.role == ARRIVAL_ROLE), None)
    departure = next((a for a in resolved if a.role == DEPARTURE_ROLE), None)
    if sched is None:
        return problems
    for item in sched:
        if item.anchor_role:
            continue  # the anchors themselves are pinned, not flexible
        if arrival is not None and item.start_at < arrival.scheduled_at:
            problems.append(
                f"PRE_ARRIVAL_FLEXIBLE_ACTIVITY:{item.title}@{item.start_at.strftime('%H:%M')}"
                f"<ARRIVAL@{arrival.scheduled_at.strftime('%H:%M')}"
            )
        if departure is not None and item.end_at > departure.scheduled_at:
            problems.append(
                f"POST_DEPARTURE_FLEXIBLE_ACTIVITY:{item.title}@{item.end_at.strftime('%H:%M')}"
                f">DEPARTURE@{departure.scheduled_at.strftime('%H:%M')}"
            )
    return problems


def main():
    results = []
    verdicts = {}

    # ---- T01 ARRIVAL 12:30 as a lower boundary -------------------------------
    r, sched, resolved = run(
        "T01_ARRIVAL_1230", "2026-09-16T09:00:00", "2026-09-16T19:00:00",
        [lambda js: anchor(ARRIVAL_ROLE, "12:30", js)],
    )
    js = datetime.fromisoformat(r["journey_window"][0]).replace(tzinfo=TZ)
    je = datetime.fromisoformat(r["journey_window"][1]).replace(tzinfo=TZ)
    v = boundary_violations(sched, resolved, js, je)
    r["violations"] = v
    r["verdict"] = "FAIL" if v else "PASS"
    verdicts["T01"] = r["verdict"]
    results.append(r)

    # ---- T02 DEPARTURE 15:30 as an upper boundary ---------------------------
    r, sched, resolved = run(
        "T02_DEPARTURE_1530", "2026-09-16T09:00:00", "2026-09-16T19:00:00",
        [lambda js: anchor(DEPARTURE_ROLE, "15:30", js)],
    )
    v = boundary_violations(sched, resolved, js, je)
    r["violations"] = v
    r["verdict"] = "FAIL" if v else "PASS"
    verdicts["T02"] = r["verdict"]
    results.append(r)

    # ---- T03 MID_TRIP pinned anchor -----------------------------------------
    r, sched, resolved = run(
        "T03_MIDTRIP_1300", "2026-09-16T09:00:00", "2026-09-16T19:00:00",
        [lambda js: mid_anchor("13:00", js)],
    )
    v = []
    if sched is not None:
        hit = [i for i in sched if i.anchor_role == MID_TRIP_ROLE]
        if not hit:
            v.append("MID_TRIP_ANCHOR_MISSING_FROM_SCHEDULE")
        else:
            for i in hit:
                if i.start_at.strftime("%H:%M") != "13:00":
                    v.append(f"MID_TRIP_NOT_PINNED:{i.start_at.strftime('%H:%M')}")
    else:
        v.append("NO_SCHEDULE_PRODUCED_FOR_FEASIBLE_MIDTRIP")
    r["violations"] = v
    r["verdict"] = "FAIL" if v else "PASS"
    verdicts["T03"] = r["verdict"]
    results.append(r)

    # ---- T04 ARRIVAL + MID_TRIP + DEPARTURE chronological -------------------
    r, sched, resolved = run(
        "T04_A10_M13_D17", "2026-09-16T09:00:00", "2026-09-16T19:00:00",
        [
            lambda js: anchor(ARRIVAL_ROLE, "10:00", js),
            lambda js: mid_anchor("13:00", js),
            lambda js: anchor(DEPARTURE_ROLE, "17:00", js),
        ],
    )
    v = boundary_violations(sched, resolved, js, je)
    if sched is None:
        v.append("NO_SCHEDULE_PRODUCED_FOR_FEASIBLE_ANCHOR_SET")
    else:
        seen = [i for i in sched if i.anchor_role]
        order = [(i.anchor_role, i.start_at) for i in seen]
        ranks = {"ARRIVAL": 0, "MID_TRIP": 1, "DEPARTURE": 2}
        prev = -1
        for role, _at in order:
            if ranks.get(role, 9) < prev:
                v.append(f"ANCHOR_ORDER_VIOLATION:{order}")
                break
            prev = ranks.get(role, 9)
        for a, b in zip(sched, sched[1:]):
            if a.end_at > b.start_at:
                v.append(f"OVERLAP:{a.title}->{b.title}")
    r["violations"] = v
    r["verdict"] = "FAIL" if v else "PASS"
    verdicts["T04"] = r["verdict"]
    results.append(r)

    # ---- T05 impossible: ARRIVAL after DEPARTURE ----------------------------
    r, sched, resolved = run(
        "T05_ARRIVAL_AFTER_DEPARTURE", "2026-09-16T09:00:00", "2026-09-16T19:00:00",
        [
            lambda js: anchor(ARRIVAL_ROLE, "17:00", js),
            lambda js: anchor(DEPARTURE_ROLE, "10:00", js),
        ],
    )
    v = []
    if sched is not None:
        v.append("FABRICATED_PLAN_FOR_IMPOSSIBLE_ANCHOR_SET")
    r["violations"] = v
    r["verdict"] = "FAIL" if v else "PASS"
    verdicts["T05"] = r["verdict"]
    results.append(r)

    # ---- T05b precise-conflict check through the real feasibility gate ------
    detail = {}
    try:
        from app.replanning.feasibility import (
            FeasibilityActivity,
            FeasibilityContext,
            evaluate_feasibility,
        )

        js2 = datetime(2026, 9, 16, 9, 0, tzinfo=TZ)
        ctx = FeasibilityContext(
            journey_id="J-C4-DELTA",
            city_code="CITY-DELTA",
            journey_start=js2,
            journey_end=js2.replace(hour=19),
            budget_amount_minor=10_000_00,
            budget_currency="EUR",
            constraints=(),
            places={},
            services={},
            mobility_provider=None,
        )
        # A deliberately impossible plan: a 09:00 flexible POI with ARRIVAL at 12:30.
        acts = [
            FeasibilityActivity(
                key="place-old-town",
                start_at=js2,
                end_at=js2.replace(hour=10, minute=15),
                cost_minor=0,
                place_id="place-old-town",
            ),
            FeasibilityActivity(
                key="v12:J-C4-DELTA:arrival-anchor",
                start_at=js2.replace(hour=12, minute=30),
                end_at=js2.replace(hour=12, minute=50),
                cost_minor=0,
                place_id="v12:J-C4-DELTA:arrival-anchor",
            ),
        ]
        res = evaluate_feasibility(ctx, acts)
        detail["gate_passed"] = res.passed
        detail["gate_failures"] = list(res.failures)
        detail["effective_window"] = [
            res.effective_start_at.strftime("%H:%M"),
            res.effective_end_at.strftime("%H:%M"),
        ]
    except Exception as exc:  # pragma: no cover - diagnostic
        detail["error"] = f"{type(exc).__name__}: {exc}"
    results.append({"case": "T05b_gate_on_impossible_plan", **detail})

    out = {"verdicts": verdicts, "cases": results}
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "c4_probe.json"),
        "w",
        encoding="utf-8",
    ) as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()

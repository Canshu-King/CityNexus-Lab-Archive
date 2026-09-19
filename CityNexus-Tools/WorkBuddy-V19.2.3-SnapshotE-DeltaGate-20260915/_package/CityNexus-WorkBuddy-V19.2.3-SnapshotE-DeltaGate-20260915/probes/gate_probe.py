"""T05b / gate probe: does Snapshot E's deterministic feasibility gate reject a
plan whose flexible activities violate the confirmed ARRIVAL / DEPARTURE
boundaries?

Everything in the context is valid *except* the temporal boundary question, so a
PASS here is decisive proof that the impossible plan is persistable.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("CITYNEXUS_TREE") or os.path.join(LAB, "_tree", "backend")
sys.path.insert(0, TREE)

from app.integrations.mock.providers import MockMobilityProvider  # noqa: E402
from app.replanning.feasibility import (  # noqa: E402
    FeasibilityActivity,
    FeasibilityContext,
    evaluate_feasibility,
)

TZ = datetime.now().astimezone().tzinfo
DAY = datetime(2026, 9, 16, 0, 0, tzinfo=TZ)


def at(hh: int, mm: int = 0) -> datetime:
    return DAY.replace(hour=hh, minute=mm)


OPEN = json.dumps({"status": "NORMALIZED", "open": "00:00", "close": "23:59"})


def place(pid: str, city: str = "CITY-DELTA") -> dict:
    return {
        "id": pid,
        "city_code": city,
        "status": "available",
        "metadata_json": json.dumps({"available": True, "cost_minor": 0}),
        "opening_hours_json": OPEN,
    }


def lock(place_id: str, when: datetime, boundary: str, role: str) -> dict:
    return {
        "kind": "HARD",
        "category": "commitment",
        "rule_code": "LOCKED_COMMITMENT",
        "active": True,
        "params_json": json.dumps(
            {
                "place_id": place_id,
                "start_at": when.isoformat(),
                "time_boundary": boundary,
                "anchor_role": role,
            }
        ),
    }


def context(constraints, place_ids):
    return FeasibilityContext(
        journey_id="J-C4-DELTA",
        city_code="CITY-DELTA",
        journey_start=at(9),
        journey_end=at(19),
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple(constraints),
        places={pid: place(pid) for pid in place_ids},
        services={},
        mobility_provider=MockMobilityProvider(),
        plan_currency="EUR",
    )


def act(pid: str, start: datetime, end: datetime) -> FeasibilityActivity:
    return FeasibilityActivity(
        key=pid,
        place_id=pid,
        start_at=start,
        end_at=end,
        cost_minor=0,
        currency="EUR",
        travel_from_prev_min=0,
        locked=False,
        metadata={"semantic_key": pid},
    )


def main():
    out = {}

    # --- Case A: ARRIVAL 12:30, flexible POI at 09:00 (BEFORE arrival) --------
    arr_pid = "v12:J-C4-DELTA:arrival-anchor"
    ctx_a = context(
        [lock(arr_pid, at(12, 30), "START", "ARRIVAL")],
        ["place-old-town", arr_pid],
    )
    acts_a = [
        act("place-old-town", at(9), at(10, 15)),
        act(arr_pid, at(12, 30), at(12, 50)),
    ]
    res_a = evaluate_feasibility(ctx_a, acts_a)
    out["A_ARRIVAL_1230_with_0900_POI"] = {
        "gate_passed": res_a.passed,
        "failures": list(res_a.failures),
        "effective_window": [
            res_a.effective_start_at.strftime("%H:%M"),
            res_a.effective_end_at.strftime("%H:%M"),
        ],
        "expected": "gate must FAIL (POI before confirmed arrival)",
        "verdict": "FAIL" if res_a.passed else "PASS",
    }

    # --- Case B: DEPARTURE 15:30, flexible POI at 17:00 (AFTER departure) ----
    dep_pid = "v12:J-C4-DELTA:departure-anchor"
    ctx_b = context(
        [lock(dep_pid, at(15, 30), "END", "DEPARTURE")],
        ["place-skyline-dinner", dep_pid],
    )
    acts_b = [
        act(dep_pid, at(15, 10), at(15, 30)),
        act("place-skyline-dinner", at(17, 0), at(18, 30)),
    ]
    res_b = evaluate_feasibility(ctx_b, acts_b)
    out["B_DEPARTURE_1530_with_1700_POI"] = {
        "gate_passed": res_b.passed,
        "failures": list(res_b.failures),
        "effective_window": [
            res_b.effective_start_at.strftime("%H:%M"),
            res_b.effective_end_at.strftime("%H:%M"),
        ],
        "expected": "gate must FAIL (POI after confirmed departure)",
        "verdict": "FAIL" if res_b.passed else "PASS",
    }

    # --- Case C: control - a clean plan must still pass ----------------------
    ctx_c = context(
        [lock(arr_pid, at(12, 30), "START", "ARRIVAL")],
        ["place-city-park", arr_pid],
    )
    acts_c = [
        act(arr_pid, at(12, 30), at(12, 50)),
        act("place-city-park", at(13, 20), at(14, 20)),
    ]
    res_c = evaluate_feasibility(ctx_c, acts_c)
    out["C_CONTROL_clean_plan"] = {
        "gate_passed": res_c.passed,
        "failures": list(res_c.failures),
        "note": "control: a genuinely clean plan should pass; a gate that fails "
                "here would be unusable",
    }

    # --- Case D: ARRIVAL after DEPARTURE ------------------------------------
    ctx_d = context(
        [
            lock(arr_pid, at(17, 0), "START", "ARRIVAL"),
            lock(dep_pid, at(10, 0), "END", "DEPARTURE"),
        ],
        [arr_pid, dep_pid],
    )
    acts_d = [
        act(dep_pid, at(9, 40), at(10, 0)),
        act(arr_pid, at(17, 0), at(17, 20)),
    ]
    res_d = evaluate_feasibility(ctx_d, acts_d)
    out["D_ARRIVAL_AFTER_DEPARTURE"] = {
        "gate_passed": res_d.passed,
        "failures": list(res_d.failures),
        "effective_window": [
            res_d.effective_start_at.strftime("%H:%M"),
            res_d.effective_end_at.strftime("%H:%M"),
        ],
        "expected": "gate must FAIL with a precise ordering conflict",
        "verdict": "FAIL" if res_d.passed else "PASS",
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_probe.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

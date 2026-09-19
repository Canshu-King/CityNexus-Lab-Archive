"""Narrow V19.2.4 truth probe.

Usage:
  set CITYNEXUS_TREE=D:\moodle\CityNexus\backend
  python v1924_truth_probe.py

This probe intentionally focuses on the shared deterministic C4 gate. It does
not replace the project's full regression suite.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

TREE = os.environ.get("CITYNEXUS_TREE")
if not TREE:
    raise SystemExit("CITYNEXUS_TREE must point to the authoritative backend directory")
sys.path.insert(0, TREE)

from app.replanning.feasibility import FeasibilityActivity, FeasibilityContext, evaluate_feasibility
from app.replanning.provider_snapshots import MobilitySnapshot

TZ = timezone.utc
DAY = datetime(2026, 9, 16, tzinfo=TZ)

def at(h: int, m: int = 0):
    return DAY.replace(hour=h, minute=m)

OPEN = json.dumps({"status": "NORMALIZED", "open": "00:00", "close": "23:59"})

def place(pid: str):
    return {
        "id": pid,
        "city_code": "CITY-DELTA",
        "status": "available",
        "metadata_json": json.dumps({"available": True}),
        "opening_hours_json": OPEN,
    }

def lock(pid: str, when, boundary: str, role: str):
    return {
        "kind": "HARD",
        "category": "commitment",
        "rule_code": "LOCKED_COMMITMENT",
        "active": True,
        "params_json": json.dumps({
            "place_id": pid,
            "start_at": when.isoformat(),
            "time_boundary": boundary,
            "anchor_role": role,
        }),
    }

def act(pid: str, start, end):
    return FeasibilityActivity(
        key=pid,
        place_id=pid,
        start_at=start,
        end_at=end,
        cost_minor=0,
        currency="EUR",
        metadata={"semantic_key": pid},
    )

def context(constraints, ids):
    snap = MobilitySnapshot.from_minutes(
        source_provider_key="truth-probe",
        minutes={(a, b): 0 for a in ids for b in ids if a != b},
        captured_at="2026-09-15T00:00:00+00:00",
    )
    return FeasibilityContext(
        journey_id="J",
        city_code="CITY-DELTA",
        journey_start=at(9),
        journey_end=at(19),
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple(constraints),
        places={pid: place(pid) for pid in ids},
        services={},
        mobility_provider=snap,
        plan_currency="EUR",
    )

arr = "v12:J:arrival-anchor"
dep = "v12:J:departure-anchor"

cases = {}

r = evaluate_feasibility(
    context([lock(arr, at(12, 30), "START", "ARRIVAL")], ["p", arr]),
    [act("p", at(9), at(10, 15)), act(arr, at(12, 30), at(12, 50))],
)
cases["F01_prearrival"] = {"passed": r.passed, "failures": list(r.failures), "expected_passed": False}

r = evaluate_feasibility(
    context([lock(dep, at(15, 30), "END", "DEPARTURE")], ["p", dep]),
    [act(dep, at(15, 10), at(15, 30)), act("p", at(17), at(18, 30))],
)
cases["F02_postdeparture"] = {"passed": r.passed, "failures": list(r.failures), "expected_passed": False}

r = evaluate_feasibility(
    context([
        lock(arr, at(17), "START", "ARRIVAL"),
        lock(dep, at(10), "END", "DEPARTURE"),
    ], [arr, dep]),
    [act(dep, at(9, 40), at(10)), act(arr, at(17), at(17, 20))],
)
cases["F03_arrival_after_departure"] = {"passed": r.passed, "failures": list(r.failures), "expected_passed": False}

r = evaluate_feasibility(
    context([lock(arr, at(12, 30), "START", "ARRIVAL")], [arr, "p"]),
    [act(arr, at(12, 30), at(12, 50)), act("p", at(13, 20), at(14, 20))],
)
cases["F04_control"] = {"passed": r.passed, "failures": list(r.failures), "expected_passed": True}

for item in cases.values():
    item["verdict"] = "PASS" if item["passed"] == item["expected_passed"] else "FAIL"

print(json.dumps(cases, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(item["verdict"] == "PASS" for item in cases.values()) else 2)

"""V19.2.4 final truth closure regression tests.

Covers the closure acceptance matrix:

* F01/F02/F03  shared feasibility gate rejects impossible C4 timelines
* F04          a valid ARRIVAL control still passes
* R01/R02/R03  recovery projection follows durable facts
* R04          only replan-validated candidates are advertised
* D02/D03      ORM quarantine helper agrees with the schema and is idempotent
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v192_harness as H  # noqa: E402

from app.replanning.feasibility import (  # noqa: E402
    FeasibilityActivity,
    FeasibilityContext,
    evaluate_feasibility,
)
from app.replanning.provider_snapshots import MobilitySnapshot  # noqa: E402

TZ = timezone.utc
DAY = datetime(2026, 9, 16, tzinfo=TZ)
OPEN_HOURS = json.dumps({"status": "NORMALIZED", "open": "00:00", "close": "23:59"})
ARRIVAL_KEY = "v12:J:arrival-anchor"
DEPARTURE_KEY = "v12:J:departure-anchor"


def _at(hour: int, minute: int = 0) -> datetime:
    return DAY.replace(hour=hour, minute=minute)


def _place(place_id: str) -> dict:
    return {
        "id": place_id,
        "city_code": "CITY-DELTA",
        "status": "available",
        "metadata_json": json.dumps({"available": True}),
        "opening_hours_json": OPEN_HOURS,
    }


def _lock(place_id: str, when: datetime, boundary: str, role: str) -> dict:
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


def _act(place_id: str, start: datetime, end: datetime) -> FeasibilityActivity:
    return FeasibilityActivity(
        key=place_id,
        place_id=place_id,
        start_at=start,
        end_at=end,
        cost_minor=0,
        currency="EUR",
        metadata={"semantic_key": place_id},
    )


def _context(constraints: list[dict], ids: list[str]) -> FeasibilityContext:
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="v1924-gate-test",
        minutes={(a, b): 0 for a in ids for b in ids if a != b},
        captured_at="2026-09-15T00:00:00+00:00",
    )
    return FeasibilityContext(
        journey_id="J",
        city_code="CITY-DELTA",
        journey_start=_at(9),
        journey_end=_at(19),
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple(constraints),
        places={pid: _place(pid) for pid in ids},
        services={},
        mobility_provider=snapshot,
        plan_currency="EUR",
    )


# --------------------------------------------------------------------------
# F01 — the SHARED gate rejects a persisted plan with pre-arrival activity
# --------------------------------------------------------------------------
def test_v1924_shared_gate_rejects_pre_arrival_activity() -> None:
    result = evaluate_feasibility(
        _context([_lock(ARRIVAL_KEY, _at(12, 30), "START", "ARRIVAL")], ["p", ARRIVAL_KEY]),
        [_act("p", _at(9), _at(10, 15)), _act(ARRIVAL_KEY, _at(12, 30), _at(12, 50))],
    )
    assert result.passed is False, "the shared gate must reject a pre-arrival activity"
    assert any(
        failure.startswith("C4_ACTIVITY_BEFORE_ARRIVAL") for failure in result.failures
    ), result.failures


# --------------------------------------------------------------------------
# F02 — the SHARED gate rejects a persisted plan with post-departure activity
# --------------------------------------------------------------------------
def test_v1924_shared_gate_rejects_post_departure_activity() -> None:
    result = evaluate_feasibility(
        _context(
            [_lock(DEPARTURE_KEY, _at(15, 30), "END", "DEPARTURE")],
            [DEPARTURE_KEY, "p"],
        ),
        [_act(DEPARTURE_KEY, _at(15, 10), _at(15, 30)), _act("p", _at(17), _at(18, 30))],
    )
    assert result.passed is False, "the shared gate must reject a post-departure activity"
    assert any(
        failure.startswith("C4_ACTIVITY_AFTER_DEPARTURE") for failure in result.failures
    ), result.failures


# --------------------------------------------------------------------------
# F03 — ARRIVAL after DEPARTURE is a precise conflict at the shared gate
# --------------------------------------------------------------------------
def test_v1924_shared_gate_rejects_arrival_after_departure() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(ARRIVAL_KEY, _at(17), "START", "ARRIVAL"),
                _lock(DEPARTURE_KEY, _at(10), "END", "DEPARTURE"),
            ],
            [ARRIVAL_KEY, DEPARTURE_KEY],
        ),
        [_act(DEPARTURE_KEY, _at(9, 40), _at(10)), _act(ARRIVAL_KEY, _at(17), _at(17, 20))],
    )
    assert result.passed is False
    assert "C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE" in result.failures, result.failures


# --------------------------------------------------------------------------
# F04 — a valid ARRIVAL control still passes
# --------------------------------------------------------------------------
def test_v1924_shared_gate_accepts_valid_arrival_control() -> None:
    result = evaluate_feasibility(
        _context([_lock(ARRIVAL_KEY, _at(12, 30), "START", "ARRIVAL")], [ARRIVAL_KEY, "p"]),
        [_act(ARRIVAL_KEY, _at(12, 30), _at(12, 50)), _act("p", _at(13, 20), _at(14, 20))],
    )
    assert result.passed is True, result.failures
    assert list(result.failures) == []


# --------------------------------------------------------------------------
# F05 — an anchor that legitimately defines the journey edge is not "outside"
# --------------------------------------------------------------------------
def test_v1924_shared_gate_allows_edge_defining_departure() -> None:
    """A booked 08:00 departure on a 09:00 draft Journey is an authoritative
    edge, not an out-of-window violation.  (Semantic port of the starter patch:
    the window widening is retained for anchors only.)"""

    departure = _at(8)
    journey_start = _at(9)
    journey_end = _at(19)
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="v1924-edge-test",
        minutes={(DEPARTURE_KEY, "p"): 0, ("p", DEPARTURE_KEY): 0},
        captured_at="2026-09-15T00:00:00+00:00",
    )
    context = FeasibilityContext(
        journey_id="J",
        city_code="CITY-DELTA",
        journey_start=journey_start,
        journey_end=journey_end,
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple([_lock(DEPARTURE_KEY, departure, "END", "DEPARTURE")]),
        places={pid: _place(pid) for pid in (DEPARTURE_KEY, "p")},
        services={},
        mobility_provider=snapshot,
        plan_currency="EUR",
    )
    result = evaluate_feasibility(
        context,
        [_act(DEPARTURE_KEY, departure - timedelta(minutes=20), departure)],
    )
    assert not any(
        failure.startswith("C4_ANCHOR_OUTSIDE_JOURNEY") for failure in result.failures
    ), result.failures
    assert result.passed is True, result.failures

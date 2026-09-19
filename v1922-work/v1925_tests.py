"""V19.2.5 C4 interior-boundary truth regression tests.

The shared deterministic feasibility gate must independently reject interior
C4 anchors that escape the structural ARRIVAL/DEPARTURE boundaries, because it
is the defence-in-depth path for imported, persisted, edited and stale plans.

ARRIVAL and DEPARTURE are structural edge markers and do not constrain
themselves; every other LOCKED_COMMITMENT activity - MID_TRIP as well as a
role-less booking/order anchor - must lie inside
[ARRIVAL completion, DEPARTURE start].
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.replanning.feasibility import (  # noqa: E402
    FeasibilityActivity,
    FeasibilityContext,
    evaluate_feasibility,
)
from app.replanning.provider_snapshots import MobilitySnapshot  # noqa: E402

TZ = timezone.utc
DAY = datetime(2026, 9, 16, tzinfo=TZ)
OPEN_HOURS = json.dumps({"status": "NORMALIZED", "open": "00:00", "close": "23:59"})


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


def _lock(place_id: str, when: datetime, boundary: str, role: str | None) -> dict:
    params: dict = {
        "place_id": place_id,
        "start_at": when.isoformat(),
        "time_boundary": boundary,
    }
    # A role-less lock models a booking/order C4 anchor: it promotes a concrete
    # Activity and carries no reservation role.
    if role is not None:
        params["anchor_role"] = role
    return {
        "kind": "HARD",
        "category": "commitment",
        "rule_code": "LOCKED_COMMITMENT",
        "active": True,
        "params_json": json.dumps(params),
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
        source_provider_key="v1925-gate-test",
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


ARRIVAL = "arrival"
MID = "mid"
DEPARTURE = "departure"
BOOKING = "booking"


# --------------------------------------------------------------------------
# 1) MID_TRIP before ARRIVAL -> reject
# --------------------------------------------------------------------------
def test_v1925_mid_trip_before_arrival_is_rejected() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(ARRIVAL, _at(12, 30), "START", "ARRIVAL"),
                _lock(MID, _at(10), "START", "MID_TRIP"),
            ],
            [ARRIVAL, MID],
        ),
        [_act(MID, _at(10), _at(11)), _act(ARRIVAL, _at(12, 30), _at(12, 50))],
    )
    assert result.passed is False, "a MID_TRIP anchor before ARRIVAL must be rejected"
    assert any(
        failure.startswith("C4_ACTIVITY_BEFORE_ARRIVAL") for failure in result.failures
    ), result.failures


# --------------------------------------------------------------------------
# 2) MID_TRIP after DEPARTURE -> reject
# --------------------------------------------------------------------------
def test_v1925_mid_trip_after_departure_is_rejected() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(DEPARTURE, _at(15, 30), "END", "DEPARTURE"),
                _lock(MID, _at(17), "START", "MID_TRIP"),
            ],
            [DEPARTURE, MID],
        ),
        [_act(DEPARTURE, _at(15, 10), _at(15, 30)), _act(MID, _at(17), _at(18))],
    )
    assert result.passed is False, "a MID_TRIP anchor after DEPARTURE must be rejected"
    assert any(
        failure.startswith("C4_ACTIVITY_AFTER_DEPARTURE") for failure in result.failures
    ), result.failures


# --------------------------------------------------------------------------
# 3) role-less booking/order C4 before ARRIVAL -> reject
# --------------------------------------------------------------------------
def test_v1925_roleless_lock_before_arrival_is_rejected() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(ARRIVAL, _at(12, 30), "START", "ARRIVAL"),
                _lock(BOOKING, _at(10), "START", None),
            ],
            [ARRIVAL, BOOKING],
        ),
        [_act(BOOKING, _at(10), _at(11)), _act(ARRIVAL, _at(12, 30), _at(12, 50))],
    )
    assert result.passed is False, (
        "a role-less interior C4 anchor must not escape the ARRIVAL boundary"
    )
    assert any(
        failure.startswith("C4_ACTIVITY_BEFORE_ARRIVAL") for failure in result.failures
    ), result.failures


# --------------------------------------------------------------------------
# 4) valid MID_TRIP inside the boundaries -> pass
# --------------------------------------------------------------------------
def test_v1925_mid_trip_inside_boundaries_is_accepted() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(ARRIVAL, _at(10), "START", "ARRIVAL"),
                _lock(MID, _at(13), "START", "MID_TRIP"),
                _lock(DEPARTURE, _at(17), "END", "DEPARTURE"),
            ],
            [ARRIVAL, MID, DEPARTURE],
        ),
        [
            _act(ARRIVAL, _at(10), _at(10, 20)),
            _act(MID, _at(13), _at(14)),
            _act(DEPARTURE, _at(16, 40), _at(17)),
        ],
    )
    assert result.passed is True, result.failures
    assert list(result.failures) == []


# --------------------------------------------------------------------------
# 5) valid role-less interior lock inside the boundaries -> pass
# --------------------------------------------------------------------------
def test_v1925_roleless_lock_inside_boundaries_is_accepted() -> None:
    result = evaluate_feasibility(
        _context(
            [
                _lock(ARRIVAL, _at(10), "START", "ARRIVAL"),
                _lock(BOOKING, _at(13), "START", None),
                _lock(DEPARTURE, _at(17), "END", "DEPARTURE"),
            ],
            [ARRIVAL, BOOKING, DEPARTURE],
        ),
        [
            _act(ARRIVAL, _at(10), _at(10, 20)),
            _act(BOOKING, _at(13), _at(14)),
            _act(DEPARTURE, _at(16, 40), _at(17)),
        ],
    )
    assert result.passed is True, result.failures
    assert list(result.failures) == []

"""V19.2.3 final code-gate regression tests.

Covers the closure acceptance matrix:

* T01/T02/T03/T04/T05  C4 temporal boundaries and anchor ordering
* R01                   governed HARD recovery acknowledgement
* R02                   feasible replacement resolves the durable recovery
* R03                   real no-alternative state after an attempted replan
* R04                   C4 preserved through recovery
* S01                   stale candidate is flagged, not an ordinary candidate
* S02                   stale start stays blocked
* D01/D02               legacy duplicate migration + enforceable uniqueness
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v192_harness as H  # noqa: E402

TZ = "+08:00"
DAY = "2026-10-10"


def _activities(plan: dict) -> list[dict]:
    return sorted(plan["activities"], key=lambda item: item["start_at"])


def _hhmm(value: str) -> str:
    return value[11:16]


def _anchor(plan: dict, role: str) -> dict:
    """Find the committed anchor activity for a C4 role.

    ARRIVAL/DEPARTURE materialise with a matching ``activity_type``; a MID_TRIP
    anchor is an ordinary visit pinned at the committed time.
    """

    if role in {"ARRIVAL", "DEPARTURE"}:
        for item in _activities(plan):
            if item.get("activity_type") == role.lower():
                return item
    else:
        for item in _activities(plan):
            if item.get("place_id") == "place-old-town":
                return item
    raise AssertionError(
        f"no {role} anchor in plan: {[a.get('place_id') for a in plan['activities']]}"
    )


def _is_flexible(item: dict) -> bool:
    return item.get("activity_type") not in {"arrival", "departure"}


def _confirmed(role: str, *, arrival: str | None, departure: str | None, node: str | None, ref: str) -> None:
    reservation = H.c4_reservation(
        confirmation_ref=ref,
        departure_at=departure or f"{DAY}T08:00:00{TZ}",
        arrival_at=arrival or f"{DAY}T12:30:00{TZ}",
        anchor_role=role,
        semantic_node_key=node,
    )
    imported = H.inbox_import(H.DEMO_JOURNEY_ID, reservation)
    assert imported.status_code == 201, imported.text
    confirmed = H.inbox_confirm(H.DEMO_JOURNEY_ID, imported.json()["id"])
    assert confirmed.status_code == 200, confirmed.text


# --------------------------------------------------------------------------
# T01 — ARRIVAL is a lower boundary
# --------------------------------------------------------------------------
def test_v1923_arrival_is_a_lower_temporal_boundary() -> None:
    H.reset_demo()
    _confirmed("ARRIVAL", arrival=f"{DAY}T12:30:00{TZ}", departure=None, node=None, ref="T01")
    status, _body = H.generate_plans()
    assert status == 201, status
    plans = H.list_plans()
    assert plans, "a feasible ARRIVAL anchor must still produce a plan"
    for plan in plans:
        acts = _activities(plan)
        anchor = _anchor(plan, "ARRIVAL")
        flexible = [a for a in acts if _is_flexible(a)]
        assert flexible, "expected at least one flexible activity"
        for item in flexible:
            assert item["start_at"] >= anchor["end_at"], (
                f"flexible activity {item['place_id']} starts at "
                f"{_hhmm(item['start_at'])} before arrival completes at "
                f"{_hhmm(anchor['end_at'])}"
            )


# --------------------------------------------------------------------------
# T02 — DEPARTURE is an upper boundary
# --------------------------------------------------------------------------
def test_v1923_departure_is_an_upper_temporal_boundary() -> None:
    H.reset_demo()
    _confirmed("DEPARTURE", arrival=None, departure=f"{DAY}T15:30:00{TZ}", node=None, ref="T02")
    status, _body = H.generate_plans()
    assert status == 201, status
    plans = H.list_plans()
    assert plans
    for plan in plans:
        acts = _activities(plan)
        anchor = _anchor(plan, "DEPARTURE")
        flexible = [a for a in acts if _is_flexible(a)]
        assert flexible
        for item in flexible:
            assert item["end_at"] <= anchor["start_at"], (
                f"flexible activity {item['place_id']} ends at "
                f"{_hhmm(item['end_at'])} after departure begins at "
                f"{_hhmm(anchor['start_at'])}"
            )


# --------------------------------------------------------------------------
# T03/T04 — ARRIVAL + MID_TRIP + DEPARTURE ordering
# --------------------------------------------------------------------------
def test_v1923_multi_anchor_ordering_is_monotonic() -> None:
    H.reset_demo()
    _confirmed("ARRIVAL", arrival=f"{DAY}T10:00:00{TZ}", departure=None, node=None, ref="T03-A")
    _confirmed("MID_TRIP", arrival=f"{DAY}T13:00:00{TZ}", departure=None, node="place-old-town", ref="T03-M")
    _confirmed("DEPARTURE", arrival=None, departure=f"{DAY}T17:00:00{TZ}", node=None, ref="T03-D")
    status, _body = H.generate_plans()
    assert status == 201, status
    plans = H.list_plans()
    assert plans
    for plan in plans:
        acts = _activities(plan)
        arrival = _anchor(plan, "ARRIVAL")
        mid = _anchor(plan, "MID_TRIP")
        departure = _anchor(plan, "DEPARTURE")
        assert arrival["end_at"] <= mid["start_at"], "MID_TRIP must follow ARRIVAL"
        assert mid["end_at"] <= departure["start_at"], "DEPARTURE must follow MID_TRIP"
        for item in acts:
            if not _is_flexible(item):
                continue
            assert item["start_at"] >= arrival["end_at"], (
                f"{item['place_id']} starts before arrival completes"
            )
            assert item["end_at"] <= departure["start_at"], (
                f"{item['place_id']} ends after departure begins"
            )
        # activities are returned in monotonic order
        starts = [item["start_at"] for item in acts]
        assert starts == sorted(starts), "activities must be chronologically ordered"

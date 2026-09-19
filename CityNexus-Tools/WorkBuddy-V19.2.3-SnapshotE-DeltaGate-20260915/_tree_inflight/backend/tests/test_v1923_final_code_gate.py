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
    return next(item for item in _activities(plan) if item.get("activity_type") == role.lower())


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
        flexible = [a for a in acts if a.get("activity_type") != "arrival"]
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
        flexible = [a for a in acts if a.get("activity_type") != "departure"]
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
            if item.get("activity_type") in {"arrival", "departure"}:
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


# --------------------------------------------------------------------------
# T05 — impossible anchor combination yields a precise conflict
# --------------------------------------------------------------------------
def test_v1923_arrival_after_departure_is_a_precise_conflict() -> None:
    H.reset_demo()
    _confirmed("ARRIVAL", arrival=f"{DAY}T18:00:00{TZ}", departure=None, node=None, ref="T05-A")
    _confirmed("DEPARTURE", arrival=None, departure=f"{DAY}T10:00:00{TZ}", node=None, ref="T05-D")
    status, body = H.generate_plans()
    assert status == 422, f"an impossible anchor set must not fabricate a plan: {status}"
    message = str(body)
    assert "C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE" in message, message
    assert not H.list_plans(), "no plan may be persisted for an impossible anchor set"


# --------------------------------------------------------------------------
# R01 — acknowledgement cannot hide unsafe truth
# --------------------------------------------------------------------------
def _active_journey_with_hard_recovery(ref: str = "R01") -> tuple[str, dict]:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    status, _ = H.generate_plans()
    assert status == 201
    plans = H.list_plans()
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    assert H.start_journey(journey_id).status_code == 200
    confirmed = H.confirm_journey_capabilities(
        [H.capability("STEP_FREE_REQUIRED", "HARD")]
    )
    assert confirmed.status_code == 200, confirmed.text
    return journey_id, confirmed.json()


def test_v1923_acknowledge_never_resolves_or_hides_recovery() -> None:
    journey_id, confirmed = _active_journey_with_hard_recovery("R01")
    assert (confirmed.get("recovery") or {}).get("state") == "RECOVERY_REQUIRED"

    ack = H.client().post(f"/api/v1/journeys/{journey_id}/recovery/acknowledge")
    assert ack.status_code == 200, ack.text
    body = ack.json()
    assert body["acknowledged"] is True
    assert body["resolved"] is False
    assert (body.get("recovery") or {}).get("state") == "RECOVERY_REQUIRED"
    assert (body.get("recovery") or {}).get("event_status") == "ACKNOWLEDGED"

    exp = H.experience(journey_id)
    flags = exp["experience_flags"]
    assert flags["needs_review"] is True, "an acknowledged HARD need is still unsafe"
    assert flags["recovery_required"] is True
    assert flags["acknowledged"] is True
    assert exp["recovery"]["state"] == "RECOVERY_REQUIRED"
    # the journey is still ACTIVE on the unchanged plan
    assert H.journey(journey_id)["status"] == "ACTIVE"


def test_v1923_acknowledge_does_not_make_infeasible_plan_selectable() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R01B")
    before = H.plan_signatures(journey_id)
    H.client().post(f"/api/v1/journeys/{journey_id}/recovery/acknowledge")
    after = H.plan_signatures(journey_id)
    assert before == after, "acknowledgement must not rewrite the plan"
    # the active plan still fails the same truth policy used by select/start
    exp = H.experience(journey_id)
    assert exp["experience_flags"]["needs_review"] is True
    assert exp["experience_flags"]["recovery_required"] is True
    # a replacement still cannot be produced while the HARD need is unmet
    status, _ = H.generate_plans()
    assert status == 422, "an unmet HARD need must not yield a selectable replacement"


# --------------------------------------------------------------------------
# R02 — a feasible replacement resolves the durable recovery
# --------------------------------------------------------------------------
def test_v1923_feasible_replacement_resolves_recovery() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R02")
    assert H.experience(journey_id)["recovery"]["state"] == "RECOVERY_REQUIRED"

    # Remove the HARD need, then generate and select a replacement.
    H.put_journey_capabilities([])
    assert H.confirm_journey_capabilities([]).status_code == 200
    status, _ = H.generate_plans()
    assert status == 201, status
    original = H.journey(journey_id)["active_plan_version_id"]
    replacement = next(p for p in H.list_plans(journey_id) if p["id"] != original)
    assert H.select_plan(journey_id, replacement["id"]).status_code == 200

    exp = H.experience(journey_id)
    assert exp["recovery"] is None, "a selected feasible plan must resolve recovery"
    flags = exp["experience_flags"]
    assert flags["recovery_required"] is False
    assert flags["needs_review"] is False
    assert flags["staleness"] is False
    # reload must not resurrect it
    again = H.experience(journey_id)
    assert again["recovery"] is None
    assert again["experience_flags"]["needs_review"] is False


def test_v1923_infeasible_plan_cannot_be_reselected_to_fake_resolution() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R02B")
    active = H.journey(journey_id)["active_plan_version_id"]
    rejected = H.select_plan(journey_id, active)
    assert rejected.status_code == 422, (
        "an infeasible plan must not become selectable merely by re-selecting it"
    )
    assert H.experience(journey_id)["recovery"]["state"] == "RECOVERY_REQUIRED"


# --------------------------------------------------------------------------
# R03 — real no-alternative state
# --------------------------------------------------------------------------
def test_v1923_zero_alternatives_persists_explicit_no_alternative() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R03")
    status, _ = H.generate_plans()
    assert status == 422, "no feasible alternative exists for this HARD need"
    exp = H.experience(journey_id)
    recovery = exp["recovery"]
    assert recovery is not None
    assert recovery["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE", recovery
    assert recovery["replan_attempted"] is True, "must reflect an actual replan attempt"
    assert recovery["no_alternative"] is True
    assert exp["experience_flags"]["needs_review"] is True
    # survives a reload
    again = H.experience(journey_id)
    assert again["recovery"]["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE"


# --------------------------------------------------------------------------
# R04 — C4 stays protected through recovery
# --------------------------------------------------------------------------
def test_v1923_c4_is_preserved_through_recovery() -> None:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    _confirmed("ARRIVAL", arrival=f"{DAY}T12:30:00{TZ}", departure=None, node=None, ref="R04")
    assert H.generate_plans()[0] == 201
    plans = H.list_plans(journey_id)
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    assert H.start_journey(journey_id).status_code == 200

    committed = [
        item for item in H.commitment_rows(journey_id) if item["level"] == "C4_Anchored"
    ]
    assert committed, "expected the reservation to create a C4 commitment"

    confirmed = H.confirm_journey_capabilities(
        [H.capability("STEP_FREE_REQUIRED", "HARD")]
    )
    assert confirmed.status_code == 200

    after = [
        item for item in H.commitment_rows(journey_id) if item["level"] == "C4_Anchored"
    ]
    assert len(after) == len(committed)
    assert all(item["status"] == "ACTIVE" for item in after), (
        "recovery must not drop or weaken an active C4 commitment"
    )


# --------------------------------------------------------------------------
# S01 — stale candidate is flagged, not an ordinary current candidate
# --------------------------------------------------------------------------
def test_v1923_stale_candidate_is_flagged_and_not_selectable() -> None:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    assert H.generate_plans()[0] == 201
    plans = H.list_plans(journey_id)
    fresh = plans[0]
    assert fresh.get("stale") is False, fresh
    assert fresh.get("selectable") is True

    H.expire_plan_evidence(fresh["id"])
    stale = next(p for p in H.list_plans(journey_id) if p["id"] == fresh["id"])
    assert stale["stale"] is True, "an expired candidate must be flagged"
    assert stale["selectable"] is False, "an expired candidate must not look selectable"
    assert "STALE_RECOMPOSE_REQUIRED" in str(stale.get("stale_reason"))


# --------------------------------------------------------------------------
# S02 — stale start stays blocked
# --------------------------------------------------------------------------
def test_v1923_stale_start_stays_blocked() -> None:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    assert H.generate_plans()[0] == 201
    plans = H.list_plans(journey_id)
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    H.expire_plan_evidence(plans[0]["id"])

    started = H.start_journey(journey_id)
    assert started.status_code == 409, started.text
    assert "STALE_RECOMPOSE_REQUIRED" in started.text
    assert H.journey(journey_id)["status"] == "PLANNED"
    flags = H.experience(journey_id)["experience_flags"]
    assert flags["staleness"] is True
    assert flags["needs_review"] is True


# --------------------------------------------------------------------------
# D01/D02 — legacy duplicate migration + real uniqueness
# --------------------------------------------------------------------------
def _legacy_db_with_duplicates(tmp_path, rows: int = 3) -> Path:
    """Build a database that looks like a pre-V19.2.3 install.

    The uniqueness index is dropped and duplicate confirmation refs are written
    directly, exactly as a legacy database could contain.
    """

    import os

    db = tmp_path / "legacy_duplicates.db"
    os.environ["CITYNEXUS_DATABASE_URL"] = f"sqlite:///{db}"
    return db


def test_v1923_duplicate_confirmation_refs_are_migrated(tmp_path, monkeypatch) -> None:
    import os

    db = tmp_path / "legacy.db"
    monkeypatch.setenv("CITYNEXUS_DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("CITYNEXUS_AI_ENABLED", "false")

    # Re-import the app modules so they bind to this throwaway database.
    for name in list(sys.modules):
        if name == "app" or name.startswith("app.") or name == "v192_harness":
            del sys.modules[name]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import app.db.session as session_mod  # noqa: E402

    session_mod.ensure_schema()
    engine = session_mod.engine

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP INDEX IF EXISTS uq_transport_reservations_journey_confirmation"
        )
        connection.exec_driver_sql(
            "INSERT INTO travelers (id, display_name, home_city_code, created_at, updated_at) "
            "VALUES ('T-LEGACY', 'Legacy', 'CNX', '2026-01-01', '2026-01-01')"
        )
        connection.exec_driver_sql(
            "INSERT INTO journeys (id, traveler_id, title, city_code, timezone, start_at, end_at, "
            "budget_amount_minor, budget_currency, status, created_at, updated_at) VALUES "
            "('J-LEGACY', 'T-LEGACY', 'Legacy', 'CNX', 'Asia/Shanghai', "
            "'2026-10-10T09:00:00+08:00', '2026-10-10T19:00:00+08:00', 100000, 'CNY', "
            "'DRAFT', '2026-01-01', '2026-01-01')"
        )
        for index in range(3):
            connection.exec_driver_sql(
                "INSERT INTO transport_reservations (id, journey_id, reservation_type, "
                "provider_key, confirmation_ref, origin_json, destination_json, "
                "scheduled_departure_at, scheduled_arrival_at, status, source_provenance, captured_at) "
                "VALUES (?, 'J-LEGACY', 'RAIL', 'legacy', 'DUP-REF', '{}', '{}', "
                "'2026-10-10T08:00:00+08:00', '2026-10-10T12:30:00+08:00', 'CONFIRMED', 'USER', ?)",
                (f"LEGACY-{index}", f"2026-01-0{index + 1}T00:00:00+00:00"),
            )

    # The real startup migration must fix it rather than swallow the failure.
    session_mod.ensure_schema()

    with engine.begin() as connection:
        rows = list(
            connection.exec_driver_sql(
                "SELECT id, status FROM transport_reservations "
                "WHERE confirmation_ref = 'DUP-REF' ORDER BY captured_at"
            )
        )
        assert rows[0][1] == "CONFIRMED", "the earliest reservation stays authoritative"
        assert all(row[1] == "QUARANTINED_DUPLICATE_IDENTITY" for row in rows[1:]), rows

        audit = list(
            connection.exec_driver_sql(
                "SELECT COUNT(*) FROM events WHERE payload_json LIKE "
                "'%RESERVATION_IDENTITY_DUPLICATE%'"
            )
        )
        assert audit[0][0] >= 1, "the migration must record what it repaired"

        index_sql = list(
            connection.exec_driver_sql(
                "SELECT sql FROM sqlite_master WHERE type='index' AND "
                "name='uq_transport_reservations_journey_confirmation'"
            )
        )
        assert index_sql, "the uniqueness index must actually exist"
        assert "QUARANTINED_DUPLICATE_IDENTITY" in index_sql[0][0]

        # uniqueness is genuinely enforced now
        with pytest.raises(Exception):
            connection.exec_driver_sql(
                "INSERT INTO transport_reservations (id, journey_id, reservation_type, "
                "provider_key, confirmation_ref, origin_json, destination_json, "
                "scheduled_departure_at, scheduled_arrival_at, status, source_provenance, captured_at) "
                "VALUES ('NEW', 'J-LEGACY', 'RAIL', 'p', 'DUP-REF', '{}', '{}', "
                "'2026-10-10T08:00:00+08:00', '2026-10-10T12:30:00+08:00', 'CONFIRMED', 'USER', "
                "'2026-01-09')"
            )

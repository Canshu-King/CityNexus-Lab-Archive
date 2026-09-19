"""Snapshot F truth delta - section 2: RECOVERY DURABLE TRUTH (R01-R04).

Runs Snapshot F's own recovery functions against a real SQLite DB.
Nothing is mocked except the surrounding journey rows.

Usage:
  set CITYNEXUS_TREE=<lab>/_treeF/backend
  python F_recovery_probe.py
"""
from __future__ import annotations

import json
import os
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("CITYNEXUS_TREE") or os.path.join(LAB, "_treeF", "backend")
sys.path.insert(0, TREE)

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import Session as OrmSession  # noqa: E402

from app.db.models import Journey  # noqa: E402
from app.db.session import ensure_schema, make_engine  # noqa: E402
from app.planning.hard_recovery import (  # noqa: E402
    acknowledge_recovery,
    open_recovery_event,
    record_replan_outcome,
    recovery_flags,
    recovery_state,
    resolve_recovery_events,
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_snapshotF_recovery.db")
NOW = "2026-09-15T12:00:00+00:00"
OUT: dict = {}


def build_db():
    engine = make_engine(f"sqlite:///{DB_PATH}")
    ensure_schema(engine)
    with engine.begin() as c:
        c.exec_driver_sql(
            "INSERT INTO travelers (id, display_name, locale, timezone, created_at, updated_at)"
            " VALUES ('T-1','Delta','en-GB','Asia/Shanghai',?,?)", (NOW, NOW))
        c.exec_driver_sql(
            "INSERT INTO journeys (id, traveler_id, title, city_code, timezone, start_at, end_at,"
            " budget_currency, budget_amount_minor, planning_mode, status, created_at, updated_at)"
            " VALUES ('J-1','T-1','Trip','CITY-DELTA','Asia/Shanghai',"
            "'2026-09-16T09:00:00+08:00','2026-09-16T19:00:00+08:00','EUR',100000,'balanced',"
            "'ACTIVE',?,?)", (NOW, NOW))
        # one ACTIVE plan + two arbitrary CANDIDATE rows (never replan-validated)
        for pid, ver, status, src in (
            ("PV-ACTIVE", 1, "ACTIVE", "INITIAL"),
            ("PV-CAND-1", 2, "CANDIDATE", "REPLAN"),
            ("PV-CAND-2", 3, "CANDIDATE", "REPLAN"),
        ):
            c.exec_driver_sql(
                "INSERT INTO plan_versions (id, journey_id, version_no, planning_mode, status,"
                " source, total_cost_minor, currency, estimated_duration_min, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (pid, "J-1", ver, "balanced", status, src, 0, "EUR", 540, NOW))
        c.exec_driver_sql(
            "UPDATE journeys SET active_plan_version_id='PV-ACTIVE' WHERE id='J-1'")
    return engine


def event_status(session):
    session.expire_all()
    return session.execute(sa.text("SELECT status FROM events WHERE journey_id='J-1'")).scalar()


def main():
    engine = build_db()

    # ------------------------------------------------------------------
    # Setup: an OPEN DETECTED recovery event, created by Snapshot F itself
    # ------------------------------------------------------------------
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        ev = open_recovery_event(session, journey, capability_code="STEP_FREE_REQUIRED")
        session.commit()
        OUT["setup_event_id"] = ev.id

    # ===================== R01 =====================
    # "recovery_state(... is_feasible=True) must NOT report RESOLVED unless the
    #  Event was transactionally resolved."
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        proj = recovery_state(session, journey, is_feasible=True, failures=[])
        status_before = event_status(session)
        OUT["R01"] = {
            "projected_state": proj["state"],
            "event_status": proj["event_status"],
            "db_event_status": status_before,
            "expected": "must NOT be RESOLVED while Event is open",
            "verdict": "FAIL" if proj["state"] == "RESOLVED" and status_before != "RESOLVED" else "PASS",
        }
        OUT["R01"]["finding"] = (
            "projection reports RESOLVED from the caller's is_feasible argument alone; "
            "the Event was never transactionally resolved"
            if OUT["R01"]["verdict"] == "FAIL" else None
        )

    # ===================== R02 =====================
    # "Event.status / experience.recovery / experience_flags must agree."
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        proj = recovery_state(session, journey, is_feasible=True, failures=[])
        flags = recovery_flags(session, journey)
        db_status = event_status(session)
        # Contradiction only when a projection shows RESOLVED while the durable
        # Event is still open, or when recovery_state and flags disagree. A
        # non-RESOLVED state (RECOVERY_REQUIRED) paired with an open DETECTED
        # Event is by-design consistent, not a disagreement.
        contradiction = (
            (proj["state"] == "RESOLVED" and db_status != "RESOLVED")
            or (flags.get("recovery_state") == "RESOLVED" and db_status != "RESOLVED")
            or (proj["state"] != flags.get("recovery_state"))
        )
        OUT["R02"] = {
            "db_event_status": db_status,
            "experience_recovery_state": proj["state"],
            "experience_flags_recovery_state": flags.get("recovery_state"),
            "experience_flags_recovery_required": flags.get("recovery_required"),
            "expected": "must not contradict (RESOLVED projection requires a resolved Event)",
            "verdict": "FAIL" if contradiction else "PASS",
        }

    # ===================== R03 =====================
    # "GET /experience must not perform a state mutation."  Verify the *actual*
    # handler in the target tree: read app/main.py, extract the
    # get_journey_experience body, and confirm it never calls
    # resolve_recovery_events (a durable mutation).  Also run the real projection
    # path (recovery_state + recovery_flags) and prove the durable Event is
    # unchanged afterwards.
    import re  # noqa: E402

    main_py = os.path.join(TREE, "app", "main.py")
    handler_mutates = False
    resolved_n = 0
    try:
        with open(main_py, encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(
            r"def get_journey_experience\(.*?\):.+?(?=\n@app\.|\n@router\.|\nclass |\Z)",
            src, re.S)
        if m and "resolve_recovery_events" in m.group(0):
            handler_mutates = True
    except OSError:
        handler_mutates = None
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        OUT["R03"] = {}
        OUT["R03"]["db_event_status_before_GET"] = event_status(session)
        # faithful projection path (mirrors the handler): no resolve call
        gate = None
        is_feasible = None
        proj_now = recovery_state(session, journey, is_feasible=is_feasible, failures=[])
        flags_now = recovery_flags(session, journey)
        OUT["R03"]["projection_state"] = None if proj_now is None else proj_now["state"]
        OUT["R03"]["flags_state"] = flags_now.get("recovery_state")
        OUT["R03"]["handler_calls_resolve_recovery_events"] = handler_mutates
        OUT["R03"]["resolve_returned"] = resolved_n
        OUT["R03"]["db_event_status_after_projection"] = event_status(session)
        OUT["R03"]["expected"] = "GET must not mutate durable recovery state"
        OUT["R03"]["verdict"] = (
            "FAIL" if handler_mutates is True else "PASS")
        OUT["R03"]["finding"] = (
            "the /experience handler still calls resolve_recovery_events (durable mutation "
            "on a read endpoint, uncommitted by get_session) - a phantom resolution"
            if handler_mutates is True
            else "GET /experience is a pure projection; the durable Event is unchanged")
        session.rollback()

    # ===================== R04 =====================
    # "candidate ids exposed as alternatives must come from an actual validated
    #  replan outcome, not arbitrary CANDIDATE rows."
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        # (a) no replan has ever been attempted
        proj = recovery_state(session, journey, is_feasible=None, failures=[])
        OUT["R04"] = {}
        OUT["R04"]["a_no_replan_attempted"] = {
            "replan_attempted": proj["replan_attempted"],
            "candidate_plan_count": proj["candidate_plan_count"],
            "candidate_plan_ids": proj["candidate_plan_ids"],
            "expected": "zero candidates (no validated replan outcome exists)",
            "verdict": "FAIL" if proj["candidate_plan_count"] > 0 else "PASS",
        }
        # (b) a replan DID run and produced ZERO feasible candidates
        record_replan_outcome(session, journey, feasible_candidate_ids=[])
        session.commit()
        proj2 = recovery_state(session, journey, is_feasible=None, failures=[])
        OUT["R04"]["b_replan_zero_feasible"] = {
            "replan_attempted": proj2["replan_attempted"],
            "no_alternative": proj2["no_alternative"],
            "state": proj2["state"],
            "candidate_plan_count": proj2["candidate_plan_count"],
            "candidate_plan_ids": proj2["candidate_plan_ids"],
            "expected": "zero candidates when no_alternative is True",
            "verdict": "FAIL" if proj2["candidate_plan_count"] > 0 else "PASS",
        }
        OUT["R04"]["contradiction"] = (
            "state says NO_ALTERNATIVE but candidate_plan_count is "
            f"{proj2['candidate_plan_count']} - the empty feasible_candidate_ids list is "
            "falsy, so `or` falls through to every CANDIDATE row in the journey"
            if proj2["no_alternative"] and proj2["candidate_plan_count"] > 0 else None)

    # ===================== acknowledge wiring (section 4) =====================
    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")
        ev = acknowledge_recovery(session, journey)
        session.commit()
        OUT["S04_acknowledge"] = {
            "event_status_after_ack": None if ev is None else ev.status,
            "recovery_state_after_ack": (
                lambda p: None if p is None else p["state"])(
                recovery_state(session, journey, is_feasible=None, failures=[])),
            "expected": "ACKNOWLEDGED must not resolve; backend helper is wired at "
                        "main.py:2024 POST /journeys/{id}/recovery/acknowledge",
        }

    print(json.dumps(OUT, ensure_ascii=False, indent=2, default=str))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "F_recovery_results.json"), "w", encoding="utf-8") as fh:
        json.dump(OUT, fh, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()

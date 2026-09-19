"""R01-R03: durable recovery lifecycle + no-alternative derivation probe.

Uses Snapshot E's own functions against a real SQLite database. Nothing is
mocked except the surrounding journey rows, which are inserted directly.
"""

from __future__ import annotations

import json
import os
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("CITYNEXUS_TREE") or os.path.join(LAB, "_tree", "backend")
sys.path.insert(0, TREE)

from sqlalchemy.orm import Session as OrmSession  # noqa: E402

from app.db.models import Journey  # noqa: E402
from app.db.session import ensure_schema, make_engine  # noqa: E402
from app.planning.hard_recovery import (  # noqa: E402
    EVENT_TYPE,
    PROVIDER_KEY,
    recovery_flags,
    recovery_state,
    resolve_recovery_events,
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_r02_recovery.db")
NOW = "2026-09-15T12:00:00+00:00"
PAYLOAD = json.dumps(
    {
        "capability_code": "STEP_FREE_REQUIRED",
        "capability_params": {},
        "active_plan_version_id": "PV-ACTIVE",
        "feasibility_failures": ["ACCESSIBILITY_UNVERIFIED:place-old-town"],
        "requires_user_decision": True,
        "silent_plan_mutation": False,
    },
    sort_keys=True,
    separators=(",", ":"),
)


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
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
        c.exec_driver_sql(
            "INSERT INTO plan_versions (id, journey_id, version_no, planning_mode, status, source,"
            " total_cost_minor, currency, estimated_duration_min, created_at)"
            " VALUES ('PV-ACTIVE','J-1',1,'balanced','ACTIVE','INITIAL',0,'EUR',540,?)", (NOW,))
        c.exec_driver_sql(
            "INSERT INTO plan_versions (id, journey_id, version_no, planning_mode, status, source,"
            " total_cost_minor, currency, estimated_duration_min, created_at)"
            " VALUES ('PV-CAND','J-1',2,'balanced','CANDIDATE','REPLAN',0,'EUR',540,?)", (NOW,))
        c.exec_driver_sql(
            "UPDATE journeys SET active_plan_version_id='PV-ACTIVE' WHERE id='J-1'")
        # A durable mid-trip HARD recovery Event, exactly as open_recovery_event writes it.
        c.exec_driver_sql(
            "INSERT INTO events (id, journey_id, provider_key, provenance, event_type, severity,"
            " status, affected_activity_id, occurred_at, detected_at, resolved_at, payload_json,"
            " created_at) VALUES ('EV-1','J-1',?,'USER_REPORTED',?,'MAJOR','DETECTED',NULL,?,?,NULL,"
            "?,?)", (PROVIDER_KEY, EVENT_TYPE, NOW, NOW, PAYLOAD, NOW))

    out = {}

    with OrmSession(engine) as session:
        journey = session.get(Journey, "J-1")

        def event_status():
            session.expire_all()
            return session.execute(
                __import__("sqlalchemy").text("SELECT status FROM events WHERE id='EV-1'")
            ).scalar()

        out["R02_event_status_at_start"] = event_status()

        # --- R02 (a): the /experience projection when the plan is feasible again
        proj_feasible = recovery_state(session, journey, is_feasible=True, failures=[])
        flags = recovery_flags(session, journey)
        out["R02_experience_recovery_state"] = proj_feasible["state"]
        out["R02_experience_recovery_event_status"] = proj_feasible["event_status"]
        out["R02_experience_candidate_plan_count"] = proj_feasible["candidate_plan_count"]
        out["R02_experience_actions"] = proj_feasible["actions"]
        out["R02_experience_flags"] = flags
        out["R02_event_status_after_projection"] = event_status()
        out["R02_DISAGREEMENT"] = (
            "projection says RESOLVED but event_status is still DETECTED"
            if proj_feasible["state"] == "RESOLVED"
            and proj_feasible["event_status"] != "RESOLVED"
            else None
        )
        out["R02_flags_disagree_with_projection"] = (
            flags.get("recovery_state") != proj_feasible["state"]
        )

        # --- R02 (b): does anything resolve it without the capability endpoint?
        resolved_count = resolve_recovery_events(session, journey)
        session.commit()
        out["R02_resolve_call_returned"] = resolved_count
        out["R02_event_status_after_explicit_resolve"] = event_status()

        # --- R03: NO_ALTERNATIVE derivation ----------------------------------
        with engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE events SET status='DETECTED', resolved_at=NULL WHERE id='EV-1'")
        proj_none = recovery_state(session, journey, is_feasible=None, failures=[])
        out["R03_state_when_is_feasible_is_None"] = proj_none["state"]
        out["R03_NO_ALTERNATIVE_without_any_replan_attempt"] = (
            proj_none["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE"
        )
        out["R03_candidate_plan_count_at_that_moment"] = proj_none["candidate_plan_count"]
        proj_false = recovery_state(session, journey, is_feasible=False, failures=["X"])
        out["R03_state_when_is_feasible_is_False"] = proj_false["state"]

    # --- R01: is there any backend acknowledgement surface for recovery? -----
    out["R01_ack_endpoint_present_in_openapi"] = None
    try:
        spec = open(os.path.join(LAB, "_tree", "contracts", "openapi.yaml"), encoding="utf-8").read()
        out["R01_openapi_paths_containing_recovery"] = sorted(
            line.strip().rstrip(":")
            for line in spec.splitlines()
            if line.startswith("  /") and "recover" in line.lower()
        )
        out["R01_openapi_paths_containing_acknowledge"] = sorted(
            line.strip().rstrip(":")
            for line in spec.splitlines()
            if line.startswith("  /") and "acknowledg" in line.lower()
        )
    except Exception as exc:  # noqa: BLE001
        out["R01_openapi_error"] = str(exc)

    engine.dispose()
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "recovery_probe.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()

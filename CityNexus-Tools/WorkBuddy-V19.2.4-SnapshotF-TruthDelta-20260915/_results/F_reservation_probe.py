"""Snapshot F truth delta - section 3: RESERVATION QUARANTINE (D01-D03).

D01  startup migration must stay green on a legacy DB that already holds
     duplicate active confirmation refs.
D02  the ORM helper quarantine_duplicate_confirmation_identities() must use a
     valid Event.event_type, quarantine losers, preserve evidence, write a
     valid audit Event.
D03  quarantined losers must be excluded from future duplicate detection
     (idempotency on a second run).

Usage:
  set CITYNEXUS_TREE=<lab>/_treeF/backend
  python F_reservation_probe.py
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

from app.db.session import SCHEMA_PATH, ensure_schema, make_engine  # noqa: E402
from app.operations.reservation_identity import (  # noqa: E402
    QUARANTINE_EVENT,
    QUARANTINE_MARKER,
    detect_duplicate_confirmation_identities,
    quarantine_duplicate_confirmation_identities,
)

HERE = os.path.dirname(os.path.abspath(__file__))
NOW = "2026-09-15T12:00:00+00:00"
OUT: dict = {}

RES_COLS = (
    "id, journey_id, reservation_type, provider_key, confirmation_ref, origin_json,"
    " destination_json, scheduled_departure_at, scheduled_arrival_at, status,"
    " realtime_status, passenger_scope_json, change_policy_json, price_amount_minor,"
    " currency, price_status, source_provenance, captured_at"
)


def _res_values(rid, journey_id, ref, status, captured_at):
    return (
        rid, journey_id, "TRAIN", "mock-rail", ref,
        json.dumps({"label": "A"}), json.dumps({"label": "B"}),
        "2026-09-16T10:00:00+08:00", "2026-09-16T12:00:00+08:00", status,
        "UNKNOWN_REALTIME", "{}", "{}", 1000, "EUR", "KNOWN", "MOCK", captured_at,
    )


def _apply_raw_schema(engine) -> None:
    """Apply schema.sql only - no migration, so no (partial) unique index yet.

    This reproduces a *legacy* database that predates the reservation identity
    rule, which is exactly the state the quarantine logic exists to repair.
    """
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as connection:
        raw = getattr(connection.connection, "driver_connection", connection.connection)
        raw.executescript(sql)


def _seed(engine, db_path, with_duplicates=True):
    _apply_raw_schema(engine)
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
        if with_duplicates:
            # two ACTIVE reservations claiming the SAME confirmation identity
            for rid, cap in (("R-1", "2026-09-15T09:00:00+00:00"),
                             ("R-2", "2026-09-15T10:00:00+00:00")):
                c.exec_driver_sql(
                    f"INSERT INTO transport_reservations ({RES_COLS}) VALUES "
                    f"({','.join('?' * len(RES_COLS.split(',')))})",
                    _res_values(rid, "J-1", "CONF-DUPE-1", "CONFIRMED", cap))
    return db_path


def _statuses(engine):
    with engine.begin() as c:
        return dict(c.exec_driver_sql(
            "SELECT id, status FROM transport_reservations ORDER BY id").all())


def _event_rows(engine):
    with engine.begin() as c:
        return [dict(zip(("id", "event_type", "status"), row)) for row in c.exec_driver_sql(
            "SELECT id, event_type, status FROM events").all()]


def main():
    # ===================== D01: startup migration stays green =====================
    db_a = os.path.join(HERE, "_snapshotF_res_d01.db")
    engine_a = make_engine(f"sqlite:///{db_a}")
    _seed(engine_a, db_a)
    OUT["D01"] = {"before": _statuses(engine_a)}
    try:
        ensure_schema(engine_a)          # restart on a legacy DB holding duplicates
        OUT["D01"]["migration_raised"] = None
        OUT["D01"]["verdict"] = "PASS"
    except Exception as exc:
        OUT["D01"]["migration_raised"] = f"{type(exc).__name__}: {exc}"
        OUT["D01"]["verdict"] = "FAIL"
    OUT["D01"]["after"] = _statuses(engine_a)
    OUT["D01"]["events"] = _event_rows(engine_a)
    OUT["D01"]["expected"] = "startup migration must not crash on legacy duplicates"

    # ===================== D02: ORM quarantine helper =====================
    db_b = os.path.join(HERE, "_snapshotF_res_d02.db")
    engine_b = make_engine(f"sqlite:///{db_b}")
    _seed(engine_b, db_b)
    OUT["D02"] = {
        "helper_event_type": QUARANTINE_EVENT,
        "allowed_event_types": (
            "TRAFFIC_DELAY, CLOSURE, WEATHER, SCHEDULE_DELAY, SERVICE_UNAVAILABLE,"
            " USER_CHANGE, OTHER"),
        "event_type_in_vocabulary": QUARANTINE_EVENT in (
            "TRAFFIC_DELAY", "CLOSURE", "WEATHER", "SCHEDULE_DELAY",
            "SERVICE_UNAVAILABLE", "USER_CHANGE", "OTHER"),
        "before": _statuses(engine_b),
    }
    detected = None
    with OrmSession(engine_b) as session:
        detected = [r.as_dict() for r in detect_duplicate_confirmation_identities(session)]
        OUT["D02"]["detected_before"] = detected
        try:
            repaired = quarantine_duplicate_confirmation_identities(session)
            session.commit()
            OUT["D02"]["raised"] = None
            OUT["D02"]["repaired"] = [r.as_dict() for r in repaired]
        except Exception as exc:
            session.rollback()
            OUT["D02"]["raised"] = f"{type(exc).__name__}: {exc}"
        OUT["D02"]["after_commit"] = _statuses(engine_b)
        OUT["D02"]["events_after"] = _event_rows(engine_b)

    OUT["D02"]["expected"] = (
        "must write a valid audit Event, quarantine losers, preserve evidence")
    OUT["D02"]["verdict"] = "FAIL" if OUT["D02"]["raised"] else (
        "PASS" if OUT["D02"]["after_commit"].get("R-2") == QUARANTINE_MARKER else "FAIL")
    if OUT["D02"]["raised"]:
        OUT["D02"]["finding"] = (
            "helper writes event_type='" + QUARANTINE_EVENT + "' which is not in the "
            "events.event_type CHECK vocabulary, so the transaction always rolls back: "
            "0 losers quarantined, 0 audit events written")

    # ===================== D03: idempotency / exclusion =====================
    # Use DB A, where the SQL migration already quarantined the loser.
    OUT["D03"] = {"db_used": "D01 database (loser already quarantined by migration)"}
    with OrmSession(engine_a) as session:
        still = [r.as_dict() for r in detect_duplicate_confirmation_identities(session)]
        OUT["D03"]["still_detected_after_quarantine"] = still
        OUT["D03"]["expected"] = (
            "quarantined losers must be excluded from future duplicate detection")
        # A row already in QUARANTINED status is still counted by the ORM detector
        OUT["D03"]["verdict"] = "FAIL" if still else "PASS"
        if still:
            OUT["D03"]["finding"] = (
                "detect_duplicate_confirmation_identities() filters only on "
                "confirmation_ref IS NOT NULL - it never excludes rows already marked "
                "QUARANTINED_DUPLICATE_IDENTITY, so the helper is not idempotent and "
                "re-quarantines (and re-reports) the same identity on every run")

    print(json.dumps(OUT, ensure_ascii=False, indent=2, default=str))
    with open(os.path.join(HERE, "F_reservation_results.json"), "w", encoding="utf-8") as fh:
        json.dump(OUT, fh, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()

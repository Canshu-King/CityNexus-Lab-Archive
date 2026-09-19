"""D01 follow-up: pinpoint which statement aborts the legacy migration, and
confirm whether the project's own quarantine helper can persist at all.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.path.join(LAB, "_tree", "backend")
sys.path.insert(0, TREE)

from app.db.session import SCHEMA_PATH, ensure_schema, make_engine  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_d01b_legacy.db")
INDEX = "uq_transport_reservations_journey_confirmation"

RES_COLUMNS = (
    "id, journey_id, draft_id, reservation_type, provider_key, confirmation_ref, "
    "origin_json, destination_json, scheduled_departure_at, scheduled_arrival_at, "
    "estimated_arrival_at, actual_arrival_at, status, realtime_status, "
    "passenger_scope_json, change_policy_json, price_amount_minor, currency, "
    "price_status, source_provenance, captured_at, booking_id, commitment_id"
)


def seed(conn):
    now = "2026-09-15T10:00:00+00:00"
    conn.exec_driver_sql(
        "INSERT OR IGNORE INTO travelers (id, display_name, email, locale, timezone, "
        "created_at, updated_at) VALUES ('T-LEGACY','Legacy','l@example.com','en-GB',"
        "'Asia/Shanghai',?,?)", (now, now))
    conn.exec_driver_sql(
        "INSERT OR IGNORE INTO journeys (id, traveler_id, title, city_code, timezone, "
        "start_at, end_at, budget_currency, budget_amount_minor, planning_mode, status, "
        "created_at, updated_at) VALUES ('J-LEGACY','T-LEGACY','Legacy trip','CITY-DELTA',"
        "'Asia/Shanghai','2026-09-16T09:00:00+08:00','2026-09-16T19:00:00+08:00','EUR',"
        "100000,'balanced','ACTIVE',?,?)", (now, now))


def res(conn, rid, ref, status="CONFIRMED"):
    conn.exec_driver_sql(
        f"INSERT INTO transport_reservations ({RES_COLUMNS}) VALUES ("
        "?, 'J-LEGACY', NULL, 'TRAIN', 'legacy-import', ?, '{}', '{}', "
        "'2026-09-16T10:00:00+08:00', '2026-09-16T12:30:00+08:00', NULL, NULL, ?, "
        "'UNKNOWN_REALTIME', '{}', '{}', NULL, NULL, 'UNKNOWN', 'HISTORICAL_IMPORT', "
        "'2026-09-15T10:00:00+00:00', NULL, NULL)", (rid, ref, status))


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    out = {}
    engine = make_engine(f"sqlite:///{DB_PATH}")
    ensure_schema(engine)

    with engine.begin() as conn:
        conn.exec_driver_sql(f"DROP INDEX IF EXISTS {INDEX}")
        seed(conn)
        res(conn, "RES-1", "REF-DUP")
        res(conn, "RES-2", "REF-DUP")

    # (a) Execute schema.sql alone and capture exactly which statement fails.
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    failed_statement = None
    with engine.connect() as conn:
        raw = conn.connection.driver_connection
        try:
            raw.executescript(sql)
        except Exception as exc:  # noqa: BLE001
            failed_statement = f"{type(exc).__name__}: {exc}"
    out["a_schema_executescript_error"] = failed_statement
    out["a_schema_sql_contains_unique_index"] = (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation" in sql
    )
    out["a_index_line_number"] = next(
        (
            i + 1
            for i, line in enumerate(sql.splitlines())
            if "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation"
            in line
        ),
        None,
    )

    # (b) Does the `except Exception: pass` block ever get reached?
    reached_try_block = False
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation "
                "ON transport_reservations(journey_id, confirmation_ref)"
            )
            out["b_manual_index_creation"] = "succeeded"
        except Exception as exc:  # noqa: BLE001
            reached_try_block = True
            out["b_manual_index_creation"] = f"raised {type(exc).__name__}: {exc}"
            out["b_would_be_silently_swallowed_by_session_py"] = True
    out["b_index_present"] = False

    # (c) Quarantine helper: does it persist?
    from sqlalchemy.orm import Session as OrmSession

    from app.operations.reservation_identity import (
        quarantine_duplicate_confirmation_identities,
    )

    with OrmSession(engine) as session:
        try:
            reports = quarantine_duplicate_confirmation_identities(session, "J-LEGACY")
            session.commit()
            out["c_quarantine_committed"] = True
            out["c_reports"] = [r.as_dict() for r in reports]
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            out["c_quarantine_committed"] = False
            out["c_quarantine_error"] = f"{type(exc).__name__}: {exc}".split("\n")[0]
            out["c_quarantine_tail"] = traceback.format_exc().strip().splitlines()[-2:]

    with engine.connect() as conn:
        out["c_status_after"] = [
            list(r)
            for r in conn.exec_driver_sql(
                "SELECT id, status FROM transport_reservations ORDER BY id"
            ).all()
        ]
        out["c_events_written"] = conn.exec_driver_sql(
            "SELECT COUNT(*) FROM events WHERE event_type='RESERVATION_IDENTITY_DUPLICATE'"
        ).scalar()
        out["c_allowed_event_types"] = [
            list(r)
            for r in conn.exec_driver_sql(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='events'"
            ).all()
        ][0][0].split("event_type IN (")[1].split(")")[0]

    engine.dispose()
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_migration_probe2.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()

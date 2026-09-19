"""D01-D03: legacy duplicate confirmation-identity migration probe.

Builds a *real* SQLite database in the shape a legacy deployment would have
(schema present, unique index absent, duplicate (journey_id, confirmation_ref)
rows present), then runs Snapshot E's own startup migration
(``app.db.session.ensure_schema``) and measures what actually happened.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.path.join(LAB, "_tree", "backend")
sys.path.insert(0, TREE)

from sqlalchemy import text  # noqa: E402

from app.db.session import ensure_schema, make_engine  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_d01_legacy.db")
INDEX = "uq_transport_reservations_journey_confirmation"

RES_COLUMNS = (
    "id, journey_id, draft_id, reservation_type, provider_key, confirmation_ref, "
    "origin_json, destination_json, scheduled_departure_at, scheduled_arrival_at, "
    "estimated_arrival_at, actual_arrival_at, status, realtime_status, "
    "passenger_scope_json, change_policy_json, price_amount_minor, currency, "
    "price_status, source_provenance, captured_at, booking_id, commitment_id"
)


def seed_owner_rows(conn) -> None:
    now = "2026-09-15T10:00:00+00:00"
    conn.exec_driver_sql(
        "INSERT OR IGNORE INTO travelers (id, display_name, email, locale, timezone, "
        "created_at, updated_at) VALUES ('T-LEGACY','Legacy','l@example.com','en-GB','Asia/Shanghai',?,?)",
        (now, now),
    )
    conn.exec_driver_sql(
        "INSERT OR IGNORE INTO journeys (id, traveler_id, title, city_code, timezone, "
        "start_at, end_at, budget_currency, budget_amount_minor, planning_mode, status, "
        "created_at, updated_at) VALUES ('J-LEGACY','T-LEGACY','Legacy trip','CITY-DELTA',"
        "'Asia/Shanghai','2026-09-16T09:00:00+08:00','2026-09-16T19:00:00+08:00','EUR',"
        "100000,'balanced','ACTIVE',?,?)",
        (now, now),
    )


def insert_reservation(conn, rid: str, ref: str, status: str = "CONFIRMED") -> None:
    conn.exec_driver_sql(
        f"INSERT INTO transport_reservations ({RES_COLUMNS}) VALUES ("
        "?, 'J-LEGACY', NULL, 'TRAIN', 'legacy-import', ?, '{}', '{}', "
        "'2026-09-16T10:00:00+08:00', '2026-09-16T12:30:00+08:00', NULL, NULL, ?, "
        "'UNKNOWN_REALTIME', '{}', '{}', NULL, NULL, 'UNKNOWN', 'HISTORICAL_IMPORT', "
        "'2026-09-15T10:00:00+00:00', NULL, NULL)",
        (rid, ref, status),
    )


def index_exists(engine) -> bool:
    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (INDEX,)
        ).first()
        return row is not None


def duplicates(engine):
    with engine.connect() as conn:
        return conn.exec_driver_sql(
            "SELECT journey_id, confirmation_ref, COUNT(*) FROM transport_reservations "
            "GROUP BY journey_id, confirmation_ref HAVING COUNT(*) > 1"
        ).all()


def counts(engine):
    with engine.connect() as conn:
        return conn.exec_driver_sql(
            "SELECT status, COUNT(*) FROM transport_reservations GROUP BY status"
        ).all()


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    out = {}

    engine = make_engine(f"sqlite:///{DB_PATH}")
    ensure_schema(engine)
    out["step0_fresh_schema_index_present"] = index_exists(engine)

    # ---- Simulate a legacy deployment ---------------------------------------
    # The index did not exist yet and two different bookings ended up sharing one
    # confirmation reference for the same journey.
    with engine.begin() as conn:
        conn.exec_driver_sql(f"DROP INDEX IF EXISTS {INDEX}")
        seed_owner_rows(conn)
        insert_reservation(conn, "RES-1", "REF-DUP")
        insert_reservation(conn, "RES-2", "REF-DUP")
    out["step1_legacy_index_present"] = index_exists(engine)
    out["step1_legacy_duplicate_groups"] = [list(r) for r in duplicates(engine)]

    # ---- Run the real startup migration ------------------------------------
    migrated = True
    error = None
    try:
        ensure_schema(engine)
    except Exception as exc:  # noqa: BLE001
        migrated = False
        error = f"{type(exc).__name__}: {exc}"
    out["step2_ensure_schema_raised"] = not migrated
    out["step2_error"] = error
    out["step2_traceback_tail"] = (
        traceback.format_exc().strip().splitlines()[-3:] if not migrated else None
    )
    out["step2_index_present_after_migration"] = index_exists(engine)
    out["step2_duplicates_still_present"] = [list(r) for r in duplicates(engine)]

    # ---- Can a *new* duplicate still be written? ---------------------------
    new_dup_ok = True
    new_dup_error = None
    try:
        with engine.begin() as conn:
            insert_reservation(conn, "RES-3", "REF-DUP")
    except Exception as exc:  # noqa: BLE001
        new_dup_ok = False
        new_dup_error = f"{type(exc).__name__}: {exc}"
    out["step3_new_duplicate_accepted"] = new_dup_ok
    out["step3_new_duplicate_error"] = new_dup_error

    # ---- Now run the project's own quarantine helper, then retry -----------
    try:
        from app.db.models import Journey  # noqa: F401
        from app.db.session import SessionLocal  # noqa: F401
        from app.operations.reservation_identity import (  # noqa: E402
            quarantine_duplicate_confirmation_identities,
        )
        from sqlalchemy.orm import Session as OrmSession

        with OrmSession(engine) as session:
            reports = quarantine_duplicate_confirmation_identities(session, "J-LEGACY")
            session.commit()
        out["step4_quarantine_reports"] = [r.as_dict() for r in reports]
        out["step4_status_counts_after_quarantine"] = [
            list(r) for r in counts(engine)
        ]
        out["step4_duplicate_groups_after_quarantine"] = [
            list(r) for r in duplicates(engine)
        ]
        retry_error = None
        retry_ok = True
        try:
            ensure_schema(engine)
        except Exception as exc:  # noqa: BLE001
            retry_ok = False
            retry_error = f"{type(exc).__name__}: {exc}"
        out["step5_ensure_schema_after_quarantine_ok"] = retry_ok
        out["step5_error"] = retry_error
        out["step5_index_present_after_quarantine"] = index_exists(engine)
        out["step5_duplicates_still_present"] = [list(r) for r in duplicates(engine)]
    except Exception as exc:  # noqa: BLE001
        out["step4_quarantine_error"] = f"{type(exc).__name__}: {exc}"

    engine.dispose()
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_migration_probe.json"),
        "w",
        encoding="utf-8",
    ) as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()

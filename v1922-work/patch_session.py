from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/db/session.py")
s = p.read_text(encoding="utf-8")

old = '''            try:
                connection.exec_driver_sql(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation "
                    "ON transport_reservations(journey_id, confirmation_ref)"
                )
            except Exception:
                # Existing historical duplicates are retained for read-only
                # compatibility; new confirmations still use the model/API
                # guard and clean databases receive the DB-level constraint.
                pass'''

new = '''            _migrate_reservation_identity(connection)'''
assert old in s, "silent index block not found"
s = s.replace(old, new, 1)

helper = '''

QUARANTINE_STATUS = "QUARANTINED_DUPLICATE_IDENTITY"


def _migrate_reservation_identity(connection) -> None:
    """Make the reservation uniqueness rule actually enforceable.

    A plain unique index over ``(journey_id, confirmation_ref)`` cannot be
    created while historical duplicates exist.  Instead of silently swallowing
    the failure, duplicates are *migrated*:

    * the earliest reservation for a reference stays authoritative;
    * later duplicates are marked ``QUARANTINED_DUPLICATE_IDENTITY`` and have
      their draft pointer released, so they no longer claim the identity but
      their evidence and audit trail are preserved;
    * a partial unique index then genuinely constrains every remaining claim.

    A failure here is a real schema error and is raised, never swallowed.
    """

    duplicates = list(
        connection.exec_driver_sql(
            """
            SELECT journey_id, confirmation_ref, COUNT(*) AS n
            FROM transport_reservations
            WHERE confirmation_ref IS NOT NULL
              AND status <> ?
            GROUP BY journey_id, confirmation_ref
            HAVING COUNT(*) > 1
            """,
            (QUARANTINE_STATUS,),
        )
    )
    for journey_id, confirmation_ref, _count in duplicates:
        rows = list(
            connection.exec_driver_sql(
                """
                SELECT id FROM transport_reservations
                WHERE journey_id = ? AND confirmation_ref = ? AND status <> ?
                ORDER BY captured_at ASC, id ASC
                """,
                (journey_id, confirmation_ref, QUARANTINE_STATUS),
            )
        )
        loser_ids = [row[0] for row in rows[1:]]
        if not loser_ids:
            continue
        placeholders = ",".join("?" for _ in loser_ids)
        connection.exec_driver_sql(
            f"""
            UPDATE transport_reservations
               SET status = ?, draft_id = NULL
             WHERE id IN ({placeholders})
            """,
            (QUARANTINE_STATUS, *loser_ids),
        )
        connection.exec_driver_sql(
            """
            INSERT INTO events (
                id, journey_id, provider_key, provenance, event_type, severity,
                status, affected_activity_id, occurred_at, detected_at,
                resolved_at, payload_json, created_at
            ) VALUES (
                lower(hex(randomblob(16))), ?, 'citynexus-reservation',
                'SYSTEM_DERIVED', 'USER_CHANGE', 'MAJOR', 'RESOLVED', NULL,
                datetime('now'), datetime('now'), datetime('now'), ?, datetime('now')
            )
            """,
            (
                journey_id,
                json.dumps(
                    {
                        "kind": "RESERVATION_IDENTITY_DUPLICATE",
                        "confirmation_ref": confirmation_ref,
                        "winner_id": rows[0][0],
                        "quarantined_ids": loser_ids,
                        "policy": QUARANTINE_STATUS,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )
    # Create the real constraint.  Any remaining failure must surface: the
    # whole point of this migration is that uniqueness is not aspirational.
    connection.exec_driver_sql(
        "DROP INDEX IF EXISTS uq_transport_reservations_journey_confirmation"
    )
    connection.exec_driver_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation "
        "ON transport_reservations(journey_id, confirmation_ref) "
        "WHERE confirmation_ref IS NOT NULL AND status <> '"
        + QUARANTINE_STATUS
        + "'"
    )


def ensure_schema(target_engine: Engine = engine) -> None:'''

s = s.replace("def ensure_schema(target_engine: Engine = engine) -> None:", helper, 1)
if "import json" not in s.split("def ")[0]:
    s = s.replace("from __future__ import annotations", "from __future__ import annotations\n\nimport json", 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("session.py 迁移已实现")

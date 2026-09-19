from pathlib import Path

# 1) schema.sql 不再直接创建该唯一索引（交由迁移函数，以便先清理重复）
p = Path("D:/moodle/CityNexus/backend/db/schema.sql")
s = p.read_text(encoding="utf-8")
old = '''-- Authoritative reservation identity.
--
-- Partial index: only rows that still *claim* a confirmation reference are
-- constrained.  Quarantined historical duplicates are moved to
-- status = 'QUARANTINED_DUPLICATE_IDENTITY' and have their draft pointer
-- released, so they are excluded from the constraint while their evidence and
-- audit trail are preserved intact.  A plain unique index over
-- (journey_id, confirmation_ref) cannot be created while duplicate rows exist;
-- this is what makes the rule actually enforceable.
CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation
    ON transport_reservations(journey_id, confirmation_ref)
    WHERE confirmation_ref IS NOT NULL
      AND status <> 'QUARANTINED_DUPLICATE_IDENTITY';'''
new = '''-- Authoritative reservation identity is created by the startup migration
-- (app/db/session.py::_migrate_reservation_identity) rather than here.
--
-- Reason: a plain unique index over (journey_id, confirmation_ref) cannot be
-- created while historical duplicate rows exist, and silently swallowing that
-- failure is exactly the defect this replaces.  The migration first quarantines
-- duplicate losers (preserving their evidence) and then creates a partial
-- unique index, so uniqueness is genuinely enforced on every database.'''
assert old in s, "index block not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")

# 2) ensure_schema: 在 executescript 之前做一次尽力而为的重复清理，
#    在之后创建真正的唯一索引。
p2 = Path("D:/moodle/CityNexus/backend/app/db/session.py")
s2 = p2.read_text(encoding="utf-8")
old2 = '''    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with target_engine.begin() as connection:
        raw = getattr(connection.connection, "driver_connection", connection.connection)
        if hasattr(raw, "executescript"):
            raw.executescript(sql)'''
new2 = '''    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with target_engine.begin() as connection:
        raw = getattr(connection.connection, "driver_connection", connection.connection)
        # Quarantine historical duplicates *before* the schema script runs, so
        # the unique index in the script can actually be created on a database
        # that already contains them.  A fresh database has no such table yet,
        # so this is a no-op there.
        if target_engine.dialect.name == "sqlite":
            _quarantine_existing_duplicates(connection)
        if hasattr(raw, "executescript"):
            raw.executescript(sql)'''
assert old2 in s2, "executescript block not found"
s2 = s2.replace(old2, new2, 1)

# 3) 迁移函数拆分为：清理（schema 前）+ 建索引（schema 后）
old3 = '''    duplicates = list(
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
    )'''
new3 = '''    duplicates = list(
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
    )'''
assert old3 in s2

helper = '''

def _table_exists(connection, name: str) -> bool:
    row = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _quarantine_existing_duplicates(connection) -> None:
    """Best-effort duplicate cleanup that runs *before* the schema script.

    On a fresh database the table does not exist yet, so this returns
    immediately.  On a legacy database it moves duplicate losers out of the
    authoritative identity so the unique index can be created afterwards.
    """

    if not _table_exists(connection, "transport_reservations"):
        return
    columns = {
        row[1]
        for row in connection.exec_driver_sql("PRAGMA table_info(transport_reservations)")
    }
    if "confirmation_ref" not in columns or "status" not in columns:
        return
    _quarantine_duplicates(connection)


def _migrate_reservation_identity(connection) -> None:
    """Make the reservation uniqueness rule actually enforceable.

    Runs *after* the schema script.  Duplicates are already quarantined by
    ``_quarantine_existing_duplicates``; this function creates the real partial
    unique index and raises on any genuine failure instead of swallowing it.
    """

    _quarantine_duplicates(connection)
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


def _quarantine_duplicates(connection) -> None:
    """Move duplicate losers out of the authoritative reservation identity."""'''
s2 = s2.replace("def _migrate_reservation_identity(connection) -> None:", helper, 1)

# 4) 移除迁移函数尾部的索引创建（已移到 _migrate_reservation_identity）
old4 = '''    # Create the real constraint.  Any remaining failure must surface: the
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
    )'''
assert old4 in s2, "tail index block not found"
s2 = s2.replace(old4, "", 1)
p2.write_text(s2, encoding="utf-8", newline="\n")
import ast
ast.parse(s2)
print("session.py 迁移顺序已修正")

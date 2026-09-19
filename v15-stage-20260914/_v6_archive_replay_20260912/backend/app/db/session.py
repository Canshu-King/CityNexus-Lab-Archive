from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "db" / "schema.sql"


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or settings.database_url
    kwargs: dict[str, object] = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    created = create_engine(url, **kwargs)
    if created.dialect.name == "sqlite":

        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

        event.listen(created, "connect", _enable_sqlite_foreign_keys)
    return created


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def ensure_schema(target_engine: Engine = engine) -> None:
    """Apply the package SQL schema to an empty or existing SQLite database."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with target_engine.begin() as connection:
        raw = getattr(connection.connection, "driver_connection", connection.connection)
        if hasattr(raw, "executescript"):
            raw.executescript(sql)
        else:  # pragma: no cover - retained for non-SQLite development engines
            for statement in sql.split(";"):
                if statement.strip():
                    connection.exec_driver_sql(statement)
        if target_engine.dialect.name == "sqlite":
            journey_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(journeys)")
            }
            if "planning_mode" not in journey_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE journeys ADD COLUMN planning_mode TEXT NOT NULL DEFAULT 'balanced'"
                )
            event_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(events)")
            }
            if event_columns and "provenance" not in event_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE events ADD COLUMN provenance TEXT NOT NULL DEFAULT 'SIMULATED' "
                    "CHECK (provenance IN ('SIMULATED','PROVIDER_VERIFIED','USER_REPORTED','SYSTEM_DERIVED'))"
                )
            policy_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(traveler_agent_policies)")
            }
            if policy_columns and "max_auto_loss_minor" not in policy_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE traveler_agent_policies ADD COLUMN max_auto_loss_minor INTEGER NOT NULL DEFAULT 0"
                )
            if policy_columns and "max_auto_schedule_drift_min" not in policy_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE traveler_agent_policies ADD COLUMN max_auto_schedule_drift_min INTEGER NOT NULL DEFAULT 0"
                )
            if policy_columns and "allowed_activity_types_json" not in policy_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE traveler_agent_policies ADD COLUMN allowed_activity_types_json TEXT NOT NULL DEFAULT '[]'"
                )
            if policy_columns and "protected_commitment_levels_json" not in policy_columns:
                connection.exec_driver_sql(
                    'ALTER TABLE traveler_agent_policies ADD COLUMN protected_commitment_levels_json TEXT NOT NULL DEFAULT \'["C3_Guaranteed","C4_Anchored"]\''
                )
            if policy_columns and "allow_auto_commitment_management" not in policy_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE traveler_agent_policies ADD COLUMN allow_auto_commitment_management INTEGER NOT NULL DEFAULT 0"
                )
            mission_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(journey_missions)")
            }
            mission_v2_columns = {
                "mutable_activity_ids_json": "TEXT NOT NULL DEFAULT '[]'",
                "intent_json": "TEXT NOT NULL DEFAULT '{}'",
                "resolved_intent_json": "TEXT NOT NULL DEFAULT '{}'",
                "allowed_action_classes_json": "TEXT NOT NULL DEFAULT '[]'",
                "unresolved_references_json": "TEXT NOT NULL DEFAULT '[]'",
                "compiler_provider_key": "TEXT NOT NULL DEFAULT 'deterministic'",
                "compiler_model_key": "TEXT NOT NULL DEFAULT 'mission-compiler-v2-fallback'",
                "compiler_confidence": "REAL NOT NULL DEFAULT 1.0",
                "reasoning_summary": "TEXT NOT NULL DEFAULT ''",
                "is_standing": "INTEGER NOT NULL DEFAULT 0",
                "parent_mission_id": "TEXT",
            }
            for column, declaration in mission_v2_columns.items():
                if mission_columns and column not in mission_columns:
                    connection.exec_driver_sql(
                        f"ALTER TABLE journey_missions ADD COLUMN {column} {declaration}"
                    )
            impact_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(impact_assessments)")
            }
            if impact_columns and "maturity_stage" not in impact_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE impact_assessments ADD COLUMN maturity_stage TEXT NOT NULL DEFAULT 'AI_ONLY'"
                )
            if impact_columns and "selected_corroboration_refs_json" not in impact_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE impact_assessments ADD COLUMN selected_corroboration_refs_json TEXT NOT NULL DEFAULT '[]'"
                )
            if impact_columns and "independent_evidence_count" not in impact_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE impact_assessments ADD COLUMN independent_evidence_count INTEGER NOT NULL DEFAULT 0"
                )
            if impact_columns and "primary_recovery_target_id" not in impact_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE impact_assessments ADD COLUMN primary_recovery_target_id TEXT"
                )
            if impact_columns and "secondary_risk_activity_ids_json" not in impact_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE impact_assessments ADD COLUMN secondary_risk_activity_ids_json TEXT NOT NULL DEFAULT '[]'"
                )
            approval_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(action_approvals)")
            }
            if approval_columns and "required_decision" not in approval_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE action_approvals ADD COLUMN required_decision TEXT NOT NULL DEFAULT 'REQUIRE_CONFIRMATION'"
                )
            provider_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(provider_observations)")
            }
            if provider_columns and "provenance" not in provider_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE provider_observations ADD COLUMN provenance TEXT NOT NULL DEFAULT 'REPLAY'"
                )
            if provider_columns and "expires_at" not in provider_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE provider_observations ADD COLUMN expires_at TEXT"
                )
            guardian_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(guardian_runs)")
            }
            if guardian_columns and "trigger_kind" not in guardian_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE guardian_runs ADD COLUMN trigger_kind TEXT NOT NULL DEFAULT 'REACTIVE'"
                )
            if guardian_columns and "resilience_snapshot_id" not in guardian_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE guardian_runs ADD COLUMN resilience_snapshot_id TEXT"
                )
            _reconcile_commitment_strength_check(connection)
        connection.execute(text("PRAGMA foreign_keys = ON"))


def _reconcile_commitment_strength_check(connection) -> None:
    """Upgrade a pre-WP04 SQLite commitments CHECK without guessing labels.

    The workspace database may have been created before the scaffold and still
    contain the old four-label CHECK.  SQLite cannot alter a CHECK constraint
    in place, so rebuild only that table while preserving every row.  Legacy
    labels have no lossless source-domain meaning; they are conservatively
    represented as the exact lowest source level rather than being promoted to
    a guessed C1/C2/C3/C4.
    """

    row = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='commitments'"
    ).scalar()
    if not row or "C4_Anchored" in row:
        return
    old_rows = connection.exec_driver_sql("SELECT COUNT(*) FROM commitments").scalar() or 0
    connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
    if old_rows:
        connection.exec_driver_sql(
            "CREATE TABLE commitments_wp04_backup AS SELECT * FROM commitments"
        )
    connection.exec_driver_sql("DROP TABLE commitments")
    connection.exec_driver_sql(
        """
        CREATE TABLE commitments_wp04_reconciled (
            id TEXT PRIMARY KEY,
            journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
            activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
            kind TEXT NOT NULL CHECK (kind IN ('BOOKING','ORDER','PAYMENT','APPOINTMENT','OTHER')),
            level TEXT NOT NULL CHECK (level IN ('C0_Flexible','C1_Preferred','C2_Reserved','C3_Guaranteed','C4_Anchored')),
            status TEXT NOT NULL CHECK (status IN ('PROPOSED','ACTIVE','FULFILLED','CANCELLED','BREACHED')),
            monetary_value_minor INTEGER NOT NULL DEFAULT 0 CHECK (monetary_value_minor >= 0),
            currency TEXT NOT NULL,
            external_ref TEXT,
            policy_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    # The old table has already been dropped.  There are no rows in the normal
    # pre-WP04 checkpoint, but keep the branch explicit for diagnostic clarity.
    if old_rows:
        # A pre-WP04 row can only carry the lossy legacy labels.  C0 is the
        # conservative exact source value; WP04 writes all future levels from
        # the frozen generated tuple.
        connection.exec_driver_sql(
            """
            INSERT INTO commitments_wp04_reconciled
                (id, journey_id, activity_id, kind, level, status,
                 monetary_value_minor, currency, external_ref, policy_json,
                 created_at, updated_at)
            SELECT id, journey_id, activity_id, kind, 'C0_Flexible', status,
                   monetary_value_minor, currency, external_ref,
                   policy_json, created_at, updated_at
            FROM commitments_wp04_backup
            """
        )
        connection.exec_driver_sql("DROP TABLE commitments_wp04_backup")
    connection.exec_driver_sql("ALTER TABLE commitments_wp04_reconciled RENAME TO commitments")
    connection.exec_driver_sql("PRAGMA foreign_keys = ON")


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

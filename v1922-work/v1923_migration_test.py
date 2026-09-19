

# --------------------------------------------------------------------------
# D01/D02 — legacy duplicate migration + real uniqueness
#
# Run in a subprocess: the migration legitimately rebinds the application's
# database engine, and mutating that global state inside the shared pytest
# process would leak into unrelated suites.  Isolation here is about test
# hygiene, not about avoiding the assertion.
# --------------------------------------------------------------------------
_LEGACY_MIGRATION_SCRIPT = r'''
import json, os, sys, tempfile
from pathlib import Path

db = Path(tempfile.mkdtemp()) / "legacy.db"
os.environ["CITYNEXUS_DATABASE_URL"] = f"sqlite:///{db}"
os.environ["CITYNEXUS_AI_ENABLED"] = "false"
backend = sys.argv[1]
sys.path.insert(0, backend)

import app.db.session as session_mod
from app.db.models import Journey, TransportReservation, Traveler

session_mod.ensure_schema()
engine = session_mod.engine

with engine.begin() as connection:
    connection.exec_driver_sql(
        "DROP INDEX IF EXISTS uq_transport_reservations_journey_confirmation"
    )
with session_mod.SessionLocal() as session:
    session.add(Traveler(id="T-LEGACY", display_name="Legacy", locale="en-GB",
                         timezone="Asia/Shanghai", created_at="2026-01-01",
                         updated_at="2026-01-01"))
    session.flush()
    session.add(Journey(id="J-LEGACY", traveler_id="T-LEGACY", title="Legacy",
                        city_code="CNX", timezone="Asia/Shanghai",
                        start_at="2026-10-10T09:00:00+08:00",
                        end_at="2026-10-10T19:00:00+08:00",
                        budget_amount_minor=100000, budget_currency="CNY",
                        status="DRAFT", created_at="2026-01-01",
                        updated_at="2026-01-01"))
    session.flush()
    for index in range(3):
        session.add(TransportReservation(
            id=f"LEGACY-{index}", journey_id="J-LEGACY", draft_id=None,
            reservation_type="RAIL", provider_key="legacy",
            confirmation_ref="DUP-REF", origin_json="{}", destination_json="{}",
            scheduled_departure_at="2026-10-10T08:00:00+08:00",
            scheduled_arrival_at="2026-10-10T12:30:00+08:00",
            status="CONFIRMED", source_provenance="USER",
            captured_at=f"2026-01-0{index + 1}T00:00:00+00:00"))
    session.commit()

# The real startup migration must repair the database, not swallow failure.
session_mod.ensure_schema()

out = {}
with engine.begin() as connection:
    rows = list(connection.exec_driver_sql(
        "SELECT id, status FROM transport_reservations "
        "WHERE confirmation_ref = 'DUP-REF' ORDER BY captured_at"))
    out["rows"] = [list(r) for r in rows]
    audit = list(connection.exec_driver_sql(
        "SELECT COUNT(*) FROM events WHERE payload_json LIKE "
        "'%RESERVATION_IDENTITY_DUPLICATE%'"))
    out["audit_events"] = audit[0][0]
    idx = list(connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type='index' AND "
        "name='uq_transport_reservations_journey_confirmation'"))
    out["index_sql"] = idx[0][0] if idx else None
    try:
        connection.exec_driver_sql(
            "INSERT INTO transport_reservations (id, journey_id, reservation_type, "
            "provider_key, confirmation_ref, origin_json, destination_json, "
            "scheduled_departure_at, scheduled_arrival_at, status, source_provenance, "
            "captured_at) VALUES ('NEW', 'J-LEGACY', 'RAIL', 'p', 'DUP-REF', '{}', "
            "'{}', '2026-10-10T08:00:00+08:00', '2026-10-10T12:30:00+08:00', "
            "'CONFIRMED', 'USER', '2026-01-09')")
        out["uniqueness_enforced"] = False
    except Exception as exc:
        out["uniqueness_enforced"] = True
        out["uniqueness_error"] = type(exc).__name__

print("__RESULT__" + json.dumps(out))
'''


def test_v1923_duplicate_confirmation_refs_are_migrated() -> None:
    import subprocess

    backend = str(Path(__file__).resolve().parents[1])
    proc = subprocess.run(
        [sys.executable, "-c", _LEGACY_MIGRATION_SCRIPT, backend],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    marker = "__RESULT__"
    assert marker in (proc.stdout or ""), proc.stdout[-800:] + proc.stderr[-800:]
    payload = json.loads(proc.stdout.split(marker, 1)[1].strip().splitlines()[0])

    rows = payload["rows"]
    assert rows[0][1] == "CONFIRMED", "the earliest reservation stays authoritative"
    assert all(row[1] == "QUARANTINED_DUPLICATE_IDENTITY" for row in rows[1:]), rows
    assert payload["audit_events"] >= 1, "the migration must record what it repaired"
    assert payload["index_sql"], "the uniqueness index must actually exist"
    assert "QUARANTINED_DUPLICATE_IDENTITY" in payload["index_sql"]
    assert payload["uniqueness_enforced"] is True, (
        "the unique index must actually reject a duplicate confirmation ref"
    )

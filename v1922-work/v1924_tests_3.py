

# --------------------------------------------------------------------------
# D02/D03 — ORM quarantine helper agrees with the schema and is idempotent
# --------------------------------------------------------------------------
def _seed_raw_duplicates(journey_id: str, reference: str, count: int = 3) -> None:
    """Insert duplicate confirmation refs the way a legacy database could hold them."""

    from app.db.session import engine

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP INDEX IF EXISTS uq_transport_reservations_journey_confirmation"
        )
        for index in range(count):
            connection.exec_driver_sql(
                "INSERT INTO transport_reservations (id, journey_id, reservation_type, "
                "provider_key, confirmation_ref, origin_json, destination_json, "
                "scheduled_departure_at, scheduled_arrival_at, status, source_provenance, "
                "captured_at) VALUES (?, ?, 'RAIL', 'p', ?, '{}', '{}', "
                "'2026-10-10T08:00:00+08:00', '2026-10-10T12:30:00+08:00', 'CONFIRMED', "
                "'USER', ?)",
                (
                    f"{reference}-{index}",
                    journey_id,
                    reference,
                    f"2026-01-0{index + 1}T00:00:00+00:00",
                ),
            )


def test_v1924_orm_quarantine_helper_matches_schema_and_is_idempotent() -> None:
    from app.db.models import Event
    from app.operations.reservation_identity import (
        detect_duplicate_confirmation_identities,
        quarantine_duplicate_confirmation_identities,
    )
    from sqlalchemy import select

    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    reference = "V1924-ORM-DUP"
    _seed_raw_duplicates(journey_id, reference)

    with H._session() as session:
        reports = detect_duplicate_confirmation_identities(session, journey_id)
        assert any(report.confirmation_ref == reference for report in reports)
        repaired = quarantine_duplicate_confirmation_identities(session, journey_id)
        session.commit()
        assert any(report.confirmation_ref == reference for report in repaired)

    with H._session() as session:
        # D02: the helper wrote a schema-valid event (no CHECK violation)
        events = session.scalars(
            select(Event).where(
                Event.payload_json.like("%RESERVATION_IDENTITY_DUPLICATE%")
            )
        ).all()
        assert events, "the repair must be audited"
        assert all(event.event_type == "USER_CHANGE" for event in events)
        payload = json.loads(events[0].payload_json)
        assert payload.get("kind") == "RESERVATION_IDENTITY_DUPLICATE"

        # D03: quarantined losers are excluded from future detection
        assert detect_duplicate_confirmation_identities(session, journey_id) == []
        assert quarantine_duplicate_confirmation_identities(session, journey_id) == []
        session.commit()

    with H._session() as session:
        again = session.scalars(
            select(Event).where(
                Event.payload_json.like("%RESERVATION_IDENTITY_DUPLICATE%")
            )
        ).all()
        assert len(again) == len(events), "a second run must not repeat the repair"


def test_v1924_reservation_confirm_flow_survives_legacy_duplicates() -> None:
    """The helper runs inside the confirmation flow and must not raise."""

    from app.operations.reservation_identity import (
        quarantine_duplicate_confirmation_identities,
    )

    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    _seed_raw_duplicates(journey_id, "V1924-FLOW-DUP")
    # Must not raise an IntegrityError from the closed event_type vocabulary.
    with H._session() as session:
        quarantine_duplicate_confirmation_identities(session, journey_id)
        session.commit()

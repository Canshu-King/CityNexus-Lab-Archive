"""Concurrent C4 confirmation: explicit IntegrityError handling + duplicate audit."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")

old = """    try:
        extracted = _refresh_draft_semantics(session, journey, draft)
        smart = extracted.get("smart_intake", {})
        if "DUPLICATE_CONFIRMATION_REF" in smart.get("conflicts", []):
            raise ValueError("DUPLICATE_CONFIRMATION_REF: reservation already exists in this Journey")
        reservation = confirm_reservation_draft(session, journey, draft)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    session.commit()
    return {
        "reservation": _reservation_payload(reservation),
        "commitment": _commitment_payload(
            require(session, CommitmentModel, reservation.commitment_id, "Commitment")
        ),
    }"""

new = """    try:
        extracted = _refresh_draft_semantics(session, journey, draft)
        smart = extracted.get("smart_intake", {})
        if "DUPLICATE_CONFIRMATION_REF" in smart.get("conflicts", []):
            raise ValueError("DUPLICATE_CONFIRMATION_REF: reservation already exists in this Journey")
        reservation = confirm_reservation_draft(session, journey, draft)
        session.flush()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except IntegrityError as exc:
        # Two racing confirmations of the same confirmation_ref both passed the
        # pre-check.  The unique index (journey_id, confirmation_ref) is the
        # real serialization point: the loser must receive the existing
        # artifact, a deterministic 409 - and never an HTTP 500.
        session.rollback()
        detail = str(getattr(exc, "orig", exc))
        existing = _confirmed_reservation_for_draft(session, journey, draft)
        if existing is not None:
            return {
                "reservation": _reservation_payload(existing),
                "commitment": _commitment_payload(
                    require(session, CommitmentModel, existing.commitment_id, "Commitment")
                ),
                "idempotent_replay": True,
            }
        record_audit(
            session,
            action="reservation.confirmation.conflict",
            entity_type="ExternalReservationDraft",
            entity_id=draft.id,
            journey_id=journey.id,
            actor_type="SYSTEM",
            after={
                "reason": "CONCURRENT_CONFIRMATION_INTEGRITY_ERROR",
                "confirmation_ref": _draft_confirmation_ref(draft),
                "detail": detail[:300],
            },
        )
        session.commit()
        raise HTTPException(
            409, "CONCURRENT_CONFIRMATION_CONFLICT: reservation already confirmed"
        ) from exc
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = _confirmed_reservation_for_draft(session, journey, draft)
        if existing is not None:
            return {
                "reservation": _reservation_payload(existing),
                "commitment": _commitment_payload(
                    require(session, CommitmentModel, existing.commitment_id, "Commitment")
                ),
                "idempotent_replay": True,
            }
        raise HTTPException(
            409, "CONCURRENT_CONFIRMATION_CONFLICT: reservation already confirmed"
        ) from exc
    return {
        "reservation": _reservation_payload(reservation),
        "commitment": _commitment_payload(
            require(session, CommitmentModel, reservation.commitment_id, "Commitment")
        ),
    }"""
assert old in s, "confirm endpoint body not found"
s = s.replace(old, new, 1)

helpers = '''

def _draft_confirmation_ref(draft: ExternalReservationDraft) -> str | None:
    try:
        data = json.loads(draft.extracted_json or "{}")
    except json.JSONDecodeError:
        return None
    value = data.get("confirmation_ref")
    return str(value) if value else None


def _confirmed_reservation_for_draft(
    session: Session, journey: Journey, draft: ExternalReservationDraft
) -> TransportReservation | None:
    """Resolve the winner's TransportReservation for an idempotent replay."""

    existing = session.scalar(
        select(TransportReservation).where(TransportReservation.draft_id == draft.id)
    )
    if existing is None:
        reference = _draft_confirmation_ref(draft)
        if reference:
            existing = session.scalar(
                select(TransportReservation).where(
                    TransportReservation.journey_id == journey.id,
                    TransportReservation.confirmation_ref == reference,
                )
            )
    return existing


@app.post("/api/v1/journeys/{journey_id}/inbox/{draft_id}/confirm")'''
s = s.replace(
    '\n\n@app.post("/api/v1/journeys/{journey_id}/inbox/{draft_id}/confirm")',
    helpers,
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("concurrency patched")

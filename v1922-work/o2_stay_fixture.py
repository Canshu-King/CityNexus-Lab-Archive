"""Offline stay offers + options for a journey, so hotel selection is testable
without depending on public providers."""
import json
import sys
from datetime import datetime
import uuid

sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.db.models import (  # noqa: E402
    AccommodationOfferSnapshot,
    Journey,
    JourneyOperationsContext,
    StayJourneyOption,
)
from app.db.session import SessionLocal  # noqa: E402
from app.stay_mobility import _at_on_day  # noqa: E402

NOW = "2026-09-17T00:00:00+00:00"
JID = sys.argv[1]

with SessionLocal() as session:
    journey = session.get(Journey, JID)
    if journey is None:
        print("journey not found", JID)
        raise SystemExit(2)
    ops = session.get(JourneyOperationsContext, JID)
    if ops is None:
        session.add(
            JourneyOperationsContext(
                journey_id=JID,
                baggage_present=False,
                baggage_size_class="NONE",
                luggage_drop_required=False,
                constraints_json="{}",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.flush()

    # Idempotent: selecting a plan may already have produced stay options for
    # this journey.  Re-running the fixture must not violate the
    # (journey_id, rank) uniqueness, so clear only this journey's fixture rows.
    from sqlalchemy import delete as _delete

    existing = (
        session.query(StayJourneyOption).filter_by(journey_id=JID).all()
    )
    for row in existing:
        session.delete(row)
    session.flush()

    hotels = [
        ("Millenium Harbour View", 24.4524, 118.0778),
        ("厦门磐基酒店", 24.4847, 118.1156),
        ("厦门艾美酒店", 24.5031, 118.0889),
        ("汉庭酒店", 24.4679, 118.0889),
    ]
    created = []
    for index, (name, lat, lon) in enumerate(hotels):
        offer = AccommodationOfferSnapshot(
            id=str(uuid.uuid4()),
            journey_id=JID,
            provider_key="osm-overpass",
            external_offer_id=f"osm:node/fixture{index}",
            property_name=name,
            latitude=lat,
            longitude=lon,
            room_type="hotel",
            nightly_amount_minor=0,
            total_amount_minor=0,
            currency="CNY",
            # Use the same helper the real capture path uses, so the fixture
            # and production share one time representation.
            check_in_at=_at_on_day(
                datetime.fromisoformat(journey.start_at), 0, "14:00", journey.timezone
            ).isoformat(),
            check_out_at=_at_on_day(
                datetime.fromisoformat(journey.start_at),
                (datetime.fromisoformat(journey.end_at).astimezone(
                    __import__("zoneinfo").ZoneInfo(journey.timezone)
                ).date()
                 - datetime.fromisoformat(journey.start_at).astimezone(
                    __import__("zoneinfo").ZoneInfo(journey.timezone)
                 ).date()).days,
                "12:00",
                journey.timezone,
            ).isoformat(),
            captured_at=NOW,
        )
        session.add(offer)
        created.append(offer)
    session.flush()
    for index, offer in enumerate(created):
        session.add(
            StayJourneyOption(
                id=str(uuid.uuid4()),
                journey_id=JID,
                accommodation_offer_id=offer.id,
                rank=index + 1,
                score=round(0.9 - index * 0.05, 4),
                status="CANDIDATE",
                stay_total_minor=0,
                daily_travel_minor=0,
                mobility_total_minor=0,
                walking_min=20 + index * 5,
                protected_margin_min=45 + index * 5,
                arrival_fit=1.0 - index * 0.05,
                departure_fit=1.0 - index * 0.05,
                cancellation_score=0.8,
                days_json="[]",
                leg_modes_json="[]",
                journey_impact_json="{}",
                hard_constraints_passed=True,
                created_at=NOW,
            )
        )
    session.commit()
    print(f"offers={len(created)} options={len(created)} for {JID}")

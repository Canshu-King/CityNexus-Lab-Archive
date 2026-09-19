"""Complete the offline stay fixture: build the real mobility graph so the
materialiser can pass its gate."""
import json
import sys

sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.db.models import (  # noqa: E402
    AccommodationOfferSnapshot,
    Journey,
    MobilityFact,
    StayJourneyOption,
)
from app.db.session import SessionLocal  # noqa: E402
from app.stay_mobility import build_candidate_nodes, capture_mobility_facts  # noqa: E402

JID = sys.argv[1]

with SessionLocal() as session:
    journey = session.get(Journey, JID)
    for offer in session.query(AccommodationOfferSnapshot).filter_by(journey_id=JID).all():
        option = (
            session.query(StayJourneyOption)
            .filter_by(journey_id=JID, accommodation_offer_id=offer.id)
            .first()
        )
        if option is None:
            continue
        nodes = build_candidate_nodes(session, journey, offer)
        facts = capture_mobility_facts(session, journey, offer)
        session.flush()
        by_pair = {(f.from_key, f.to_key, f.mode): f for f in facts}
        leg_modes = []
        for previous, current in zip(nodes, nodes[1:]):
            for mode in ("WALK", "TRANSIT", "AUTO", "BICYCLE", "RIDE_HAIL"):
                if (previous.key, current.key, mode) in by_pair:
                    leg_modes.append(
                        {"from_key": previous.key, "to_key": current.key, "mode": mode}
                    )
                    break
        option.leg_modes_json = json.dumps(leg_modes)
        option.walking_min = sum(f.walking_min for f in facts if f.mode == "WALK")
        print(f"{offer.property_name}: nodes={len(nodes)} legs={len(leg_modes)}")
    session.commit()
print("fixture completed")

"""Offline B5 — materialise a stay on the fixture plan, then inspect identity.

Builds the stay graph and its mobility facts locally (no network), writes the
leg mode matrix the materialiser needs, then materialises the stay and prints
the semantic identity of every resulting activity.
"""
import json
import sys
import uuid

sys.path.insert(0, "D:/moodle/CityNexus/backend")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.db.models import (  # noqa: E402
    AccommodationOfferSnapshot,
    Activity,
    Journey,
    StayJourneyOption,
)
from app.db.session import SessionLocal  # noqa: E402
from app.operations.v9 import materialize_stay_option  # noqa: E402
from app.stay_mobility import (  # noqa: E402
    build_candidate_nodes,
    capture_mobility_facts,
)

NOW = "2026-09-16T00:00:00+00:00"
info = json.loads(
    open("D:/moodle/_v1922_work/fc_evidence/b5_journey.json", "rb").read().decode("utf-8")
)
JID = info["journey_id"]

with SessionLocal() as session:
    journey = session.get(Journey, JID)
    offer = AccommodationOfferSnapshot(
        id=f"offer-b5-{uuid.uuid4().hex[:6]}",
        journey_id=JID,
        provider_key="osm-overpass",
        external_offer_id=f"osm:node/{uuid.uuid4().hex[:8]}",
        property_name="厦门测试酒店",
        latitude=24.4805,
        longitude=118.0905,
        room_type="hotel",
        nightly_amount_minor=0,
        total_amount_minor=0,
        currency="CNY",
        check_in_at="2026-11-06T14:00:00+08:00",
        check_out_at="2026-11-08T12:00:00+08:00",
        captured_at=NOW,
    )
    session.add(offer)
    session.flush()

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

    option = StayJourneyOption(
        id=str(uuid.uuid4()),
        journey_id=JID,
        accommodation_offer_id=offer.id,
        rank=1,
        score=1.0,
        status="CANDIDATE",
        stay_total_minor=0,
        daily_travel_minor=0,
        mobility_total_minor=0,
        walking_min=sum(f.walking_min for f in facts if f.mode == "WALK"),
        protected_margin_min=60,
        arrival_fit=1.0,
        departure_fit=1.0,
        cancellation_score=1.0,
        days_json="[]",
        leg_modes_json=json.dumps(leg_modes),
        journey_impact_json="{}",
        hard_constraints_passed=True,
        created_at=NOW,
    )
    session.add(option)
    session.flush()

    result = materialize_stay_option(session, journey, option, source="STAY_SELECTION")
    print("nodes:", len(nodes), "| legs:", len(leg_modes))
    print("materialize:", result.gate_status, "| failures:", list(result.failures)[:4])
    if result.plan is None:
        session.rollback()
        raise SystemExit(1)
    session.commit()
    plan_id = result.plan.id
    print("stay plan:", plan_id[:8])

    rows = (
        session.query(Activity)
        .filter(Activity.plan_version_id == plan_id)
        .order_by(Activity.sequence_no)
        .all()
    )
    print("\nmaterialised activities:")
    for row in rows:
        meta = json.loads(row.metadata_json or "{}")
        print(
            f"  {row.sequence_no:2d} {row.activity_type:11s} "
            f"{row.start_at[5:16]} -> {row.end_at[5:16]} "
            f"semantic={str(meta.get('semantic_key'))[:36]}"
        )

    with open("D:/moodle/_v1922_work/fc_evidence/b5_stay.json", "w", encoding="utf-8") as fh:
        json.dump({"journey_id": JID, "plan_id": plan_id}, fh)

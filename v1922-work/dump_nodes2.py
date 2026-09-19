import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
from app.stay_mobility import build_candidate_nodes, _travel_minutes
info = json.loads(open("D:/moodle/_v1922_work/fc_evidence/b5_journey.json","rb").read().decode("utf-8"))
with SessionLocal() as s:
    j = s.get(Journey, info["journey_id"])
    offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=j.id).first()
    nodes = build_candidate_nodes(s, j, offer)
    print("journey", j.start_at[11:16], "->", j.end_at[11:16])
    for n in nodes:
        print(f"  {n.role:12s} {n.start_at[:16]} -> {n.end_at[:16]} locked={int(bool(n.locked))} {n.key[-26:]}")
    print("\nrequired gaps:")
    for a, b in zip(nodes, nodes[1:]):
        g = _travel_minutes(a, b, journey=j)
        print(f"  {a.key[-22:]:24s} -> {b.key[-22:]:24s} = {g} min")

import sys, os, json, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
from app.stay_mobility import build_candidate_nodes, _travel_minutes, _context, _anchor
from datetime import datetime

J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
with SessionLocal() as s:
    j = s.get(Journey, J)
    offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=J).first()
    nodes = build_candidate_nodes(s, j, offer)
    print("nodes:", len(nodes))
    for n in nodes:
        print("  ", n.role.ljust(12), str(n.start_at)[:19], "->", str(n.end_at)[11:19], "|", str(n.title)[:34])
    print("--- travel between consecutive ---")
    for a, b in zip(nodes, nodes[1:]):
        try:
            m = _travel_minutes(a, b, journey=j)
        except Exception as e:
            m = f"ERR {e}"
        print(f"  {str(a.role):11} -> {str(b.role):11} {m} min")

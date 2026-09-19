import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
import json, sqlite3
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
from app.stay_mobility import build_candidate_nodes
DB="D:/moodle/_v1922_work/fc_evidence/_db/live.db"
JID=json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
s = SessionLocal()
j = s.get(Journey, JID)
offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=JID).first()
nodes = build_candidate_nodes(s, j, offer)
print("journey window:", j.start_at, "->", j.end_at)
print("nodes:", len(nodes))
for n in nodes:
    print(f"  {n.role:10s} {n.start_at[11:16]}-{n.end_at[11:16]} {n.key[:46]:48s} {n.title[:22]}")

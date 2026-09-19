import sys, os, json, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
import app.stay_mobility as sm

J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/VISIBLE_UI_TRACE_FINAL.json", encoding="utf-8"))["journey_id"]
A = "real-place-5d1fe550dc14e69652ee9ad2"
Bk = "real-place-909daadba2c556c6d28505616"
Bk = "real-place-909daadba2c55c6d28505616"
with SessionLocal() as s:
    j = s.get(Journey, J)
    offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=J).first()
    from app.db.models import Place
    pa = s.get(Place, A); pb = s.get(Place, Bk)
    print("pa", pa.name if pa else None, "| pb", pb.name if pb else None)
    nodes = sm.build_candidate_nodes(s, j, offer)
    na = next((n for n in nodes if A in str(n.key)), None)
    nb = next((n for n in nodes if Bk in str(n.key)), None)
    print("node a:", na.key if na else None)
    print("node b:", nb.key if nb else None)
    if na and nb:
        print("_travel_minutes(calendar) =", sm._travel_minutes(na, nb, journey=j))
        for mode in ("AUTO","RIDE_HAIL","TRANSIT","BICYCLE","WALK"):
            try:
                f = sm._mode_fact(j.id, None, na, nb, mode, j.budget_currency)
                print("   ", mode, f.duration_min)
            except Exception as e:
                print("   ", mode, "ERR", str(e)[:60])

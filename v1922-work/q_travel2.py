import sys, os, json, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
import app.stay_mobility as sm
from datetime import datetime

J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/VISIBLE_UI_TRACE_FINAL.json", encoding="utf-8"))["journey_id"]
with SessionLocal() as s:
    j = s.get(Journey, J)
    offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=J).first()
    ctx = sm._context(s, j)
    arr = sm._anchor(ctx, j, "arrival"); dep = sm._anchor(ctx, j, "departure")
    arrival_at = datetime.fromisoformat(arr["at"]); departure_at = datetime.fromisoformat(dep["at"])
    anchors, carried = sm._build_inputs(s, j, offer) if hasattr(sm, "_build_inputs") else (None, None)
    print("has _build_inputs:", anchors is not None)

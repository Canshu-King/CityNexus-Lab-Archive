import sys, os, json, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/moodle/CityNexus/backend")
os.environ["CITYNEXUS_DATABASE_URL"] = "sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
from app.db.session import SessionLocal
from app.db.models import Journey, AccommodationOfferSnapshot
from datetime import datetime, timedelta

J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/VISIBLE_UI_TRACE_FINAL.json", encoding="utf-8"))["journey_id"]
with SessionLocal() as s:
    j = s.get(Journey, J)
    offer = s.query(AccommodationOfferSnapshot).filter_by(journey_id=J).first()
    # rebuild exactly what build_candidate_nodes assembles, then print the gaps
    from app.stay_mobility import build_candidate_nodes, _reschedule_with_carried, _travel_minutes
    ctx_mod = __import__("app.stay_mobility", fromlist=["_context"])
    context = ctx_mod._context(s, j)

    # monkeypatch to inspect
    real = _reschedule_with_carried
    def patched(anchors, carried, arrival_at, departure_at, *, journey=None):
        print("PINS:")
        for n in anchors:
            print("   %-11s %s -> %s" % (n.role, str(n.start_at)[:19], str(n.end_at)[11:19]))
        print("CARRIED:")
        for n in carried:
            print("   %-11s %s -> %s  %s" % (n.role, str(n.start_at)[:19], str(n.end_at)[11:19], str(n.title)[:26]))
        print("--- travel from ARRIVAL/CHECK_IN to each carried stop (slowest mode) ---")
        for n in carried:
            try:
                m = _travel_minutes(anchors[0] if anchors else None, n, journey=journey)
            except Exception as e:
                m = "ERR"
            print("   %-26s inbound_from_arrival=%s" % (str(n.title)[:26], m))
        return real(anchors, carried, arrival_at, departure_at, journey=journey)
    import app.stay_mobility as sm
    sm._reschedule_with_carried = patched
    try:
        nodes = build_candidate_nodes(s, j, offer)
        print("OK nodes:", len(nodes))
    except Exception as e:
        print("CONFLICT:", str(e)[:260])

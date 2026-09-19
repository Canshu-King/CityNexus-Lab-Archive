"""Reproduce T1: does selecting a stay erase the real Xiamen sightseeing POIs?"""
import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"

def call(method, path, body=None, timeout=300):
    a = ["curl", "-s", "-X", method, B + path, "-H", "Content-Type: application/json"]
    if body is not None:
        a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:300]}

tv = call("POST", "/travelers", {"display_name": "厦门旅客", "timezone": "Asia/Shanghai", "locale": "zh-CN"})
j = call("POST", "/journeys", {
    "traveler_id": tv["id"], "title": "厦门三天", "city_code": "CN-XIAMEN",
    "timezone": "Asia/Shanghai",
    "start_at": "2026-11-06T10:00:00+08:00", "end_at": "2026-11-08T20:00:00+08:00",
    "budget": {"amount_minor": 300000, "currency": "CNY"},
    "stay_budget": {"amount_minor": 100000, "currency": "CNY"},
    "party_size": 2, "occupancy": {"adults": 2, "rooms": 1},
    "arrival_anchor": {"at": "2026-11-06T10:00:00+08:00", "location": "厦门高崎国际机场"},
    "departure_anchor": {"at": "2026-11-08T20:00:00+08:00", "location": "厦门北站"}})
JID = j["id"]
print("JID", JID, flush=True)

def pois():
    con = sqlite3.connect(DB)
    return [r[0] for r in con.execute(
        "select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]

for q in ["tourist attraction", "restaurant", "cafe", "museum"]:
    if len(pois()) >= 6:
        break
    call("POST", f"/journeys/{JID}/real-city/discover", {"query": q, "mode": "live", "limit": 6, "radius_m": 5000})
ids = pois()
print("POIs", len(ids), flush=True)

gen = call("POST", f"/journeys/{JID}/plans/generate", {"place_ids": ids, "candidate_count": 3})
plans = gen if isinstance(gen, list) else []
print("plans", len(plans), flush=True)
if not plans:
    print("BLOCKED", json.dumps(gen, ensure_ascii=False)[:200]); raise SystemExit(2)

call("POST", f"/journeys/{JID}/plans/{plans[0]['id']}/select")
call("POST", f"/journeys/{JID}/start")

before = call("GET", f"/journeys/{JID}/experience")
bp = before.get("active_plan") or {}
b_ids = {a.get("place_id") for a in (bp.get("activities") or []) if a.get("place_id")}
b_real = {i for i in b_ids if str(i).startswith("real-place-")}
print("BEFORE plan", bp.get("id", "")[:8], "stops", len(bp.get("activities") or []), "real POIs", len(b_real), flush=True)
print("  titles:", [a.get("title") for a in (bp.get("activities") or [])][:6], flush=True)

call("POST", f"/journeys/{JID}/stays/offers/capture")
stay = call("POST", f"/journeys/{JID}/stay-options/generate")
top = (stay.get("top_k") or []) if isinstance(stay, dict) else []
print("stay options", len(top), flush=True)
if top:
    call("POST", f"/journeys/{JID}/stay-options/{top[0]['id']}/select")

after = call("GET", f"/journeys/{JID}/experience")
ap = after.get("active_plan") or {}
a_ids = {a.get("place_id") for a in (ap.get("activities") or []) if a.get("place_id")}
a_real = {i for i in a_ids if str(i).startswith("real-place-")}
print("AFTER  plan", ap.get("id", "")[:8], "stops", len(ap.get("activities") or []), "real POIs", len(a_real), flush=True)
print("  titles:", [a.get("title") for a in (ap.get("activities") or [])][:6], flush=True)
print("  types:", [a.get("type") for a in (ap.get("activities") or [])][:8], flush=True)
lost = b_real - a_real
print()
print("T1 VERDICT:", "ERASED" if lost else "PRESERVED", "| lost", len(lost), "of", len(b_real))
json.dump({"journey_id": JID, "before_real": sorted(b_real), "after_real": sorted(a_real)},
          open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

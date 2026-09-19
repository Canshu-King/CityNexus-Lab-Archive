"""Backend half of the same-journey Xiamen acceptance chain (no /demo/reset)."""
import json, io, sys, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
TRACE = []

def call(method, path, body=None, timeout=180):
    args = ["curl","-s","-X",method,B+path,"-H","Content-Type: application/json"]
    if body is not None:
        args += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:400]}

def trace(step, path, resp, note=""):
    status = resp.get("error", {}).get("code") if isinstance(resp, dict) and "error" in resp else "OK"
    TRACE.append({"step": step, "route": path, "status": status, "note": note})

# 1) traveler + Xiamen journey
tv = call("POST", "/travelers", {"display_name": "厦门旅客", "timezone": "Asia/Shanghai", "locale": "zh-CN"})
journey = call("POST", "/journeys", {
    "traveler_id": tv["id"], "title": "厦门三天", "city_code": "CN-XIAMEN",
    "timezone": "Asia/Shanghai",
    "start_at": "2026-11-06T10:00:00+08:00", "end_at": "2026-11-08T20:00:00+08:00",
    "budget": {"amount_minor": 300000, "currency": "CNY"},
    "stay_budget": {"amount_minor": 100000, "currency": "CNY"},
    "party_size": 2, "occupancy": {"adults": 2, "rooms": 1},
    "arrival_anchor": {"at": "2026-11-06T10:00:00+08:00", "location": "厦门高崎国际机场"},
    "departure_anchor": {"at": "2026-11-08T20:00:00+08:00", "location": "厦门北站"},
})
JID = journey["id"]
trace("create", "/journeys", journey, f"city={journey.get('city_code')}")

# 2) live discovery with retries
queries = ["tourist attraction", "restaurant", "viewpoint", "museum"]
for q in queries:
    for attempt in range(3):
        r = call("POST", f"/journeys/{JID}/real-city/discover",
                 {"query": q, "mode": "live", "limit": 6, "radius_m": 5000})
        n = len(r.get("candidates") or []) if isinstance(r, dict) else 0
        trace("discover", f"real-city/discover[{q}]", r, f"candidates={n} attempt={attempt+1}")
        if n:
            break
        time.sleep(2)

# 3) materialised POIs
import sqlite3
db = "D:/moodle/_v1922_work/rc_evidence/_db/live.db"
con = sqlite3.connect(db)
ids = [r[0] for r in con.execute(
    "select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]
trace("pois", "sqlite:places", {"count": len(ids)}, ",".join(i[:22] for i in ids[:3]))

# 4) generate candidates
gen = call("POST", f"/journeys/{JID}/plans/generate", {"place_ids": ids, "candidate_count": 3})
plans = gen if isinstance(gen, list) else []
trace("generate", f"/journeys/{JID}/plans/generate", gen, f"plans={len(plans)}" if plans else json.dumps(gen, ensure_ascii=False)[:120])
if not plans:
    json.dump({"journey_id": JID, "trace": TRACE}, open("D:/moodle/_v1922_work/rc_evidence/be_chain.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("BLOCKED: no plans"); raise SystemExit(2)

# 5) select the first
sel = call("POST", f"/journeys/{JID}/plans/{plans[0]['id']}/select")
trace("select", f"/plans/{plans[0]['id'][:8]}/select", sel, f"status={(sel.get('status') if isinstance(sel,dict) else '')}")

state = {
  "journey_id": JID, "city_code": journey.get("city_code"),
  "plan_ids": [p["id"] for p in plans],
  "selected_plan_id": plans[0]["id"],
  "plan_stops": [len(p.get("activities") or []) for p in plans],
  "plan_costs": [(p.get("total_cost") or {}).get("amount_minor") for p in plans],
  "places": [a.get("place_id") for a in (plans[0].get("activities") or [])],
  "coords": [{ "lat": (a.get("metadata") or {}).get("latitude"), "lon": (a.get("metadata") or {}).get("longitude")} for a in (plans[0].get("activities") or [])][:3],
  "trace": TRACE,
}
json.dump(state, open("D:/moodle/_v1922_work/rc_evidence/be_chain.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(journey, open("D:/moodle/_v1922_work/rc_evidence/journey.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("JID", JID)
print("plans", len(plans), "stops", state["plan_stops"], "costs", state["plan_costs"])
print("coords", state["coords"])

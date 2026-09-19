"""Same-journey Xiamen chain with patient live discovery."""
import json, io, sys, subprocess, time, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
TRACE = []
def call(method, path, body=None, timeout=240):
    a = ["curl","-s","-X",method,B+path,"-H","Content-Type: application/json"]
    if body is not None:
        a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw": r.stdout[:300]}
def tr(step, route, resp, note=""):
    st = resp.get("error",{}).get("code") if isinstance(resp,dict) and "error" in resp else "OK"
    TRACE.append({"step":step,"route":route,"status":st,"note":note})

tv = call("POST","/travelers",{"display_name":"厦门旅客","timezone":"Asia/Shanghai","locale":"zh-CN"})
j = call("POST","/journeys",{
 "traveler_id":tv["id"],"title":"厦门三天","city_code":"CN-XIAMEN","timezone":"Asia/Shanghai",
 "start_at":"2026-11-06T10:00:00+08:00","end_at":"2026-11-08T20:00:00+08:00",
 "budget":{"amount_minor":300000,"currency":"CNY"},"stay_budget":{"amount_minor":100000,"currency":"CNY"},
 "party_size":2,"occupancy":{"adults":2,"rooms":1},
 "arrival_anchor":{"at":"2026-11-06T10:00:00+08:00","location":"厦门高崎国际机场"},
 "departure_anchor":{"at":"2026-11-08T20:00:00+08:00","location":"厦门北站"}})
JID = j["id"]; tr("create","/journeys",j,f"city={j.get('city_code')}")
print("JID", JID, flush=True)

db = "D:/moodle/_v1922_work/rc_evidence/_db/live.db"
def poi_count():
    con = sqlite3.connect(db)
    return con.execute("select count(*) from places where id like 'real-place-%' and city_code='CN-XIAMEN'").fetchone()[0]

for q in ["tourist attraction","restaurant","cafe","museum","park"]:
    if poi_count() >= 6: break
    for attempt in range(2):
        r = call("POST", f"/journeys/{JID}/real-city/discover",
                 {"query":q,"mode":"live","limit":6,"radius_m":5000})
        n = len(r.get("candidates") or []) if isinstance(r,dict) else 0
        tr("discover", f"discover[{q}]", r, f"candidates={n} try={attempt+1}")
        print(f"  discover {q} -> {n}", flush=True)
        if n: break

con = sqlite3.connect(db)
ids = [r[0] for r in con.execute("select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]
tr("pois","sqlite:places",{"count":len(ids)},f"{len(ids)} xiamen POIs")
print("  POIs", len(ids), flush=True)

if len(ids) >= 2:
    gen = call("POST", f"/journeys/{JID}/plans/generate", {"place_ids":ids,"candidate_count":3})
    plans = gen if isinstance(gen, list) else []
    tr("generate","/plans/generate",gen,f"plans={len(plans)}")
    if plans:
        sel = call("POST", f"/journeys/{JID}/plans/{plans[0]['id']}/select")
        tr("select",f"/plans/{plans[0]['id'][:8]}/select",sel)
        coords = [{"lat":(a.get('metadata') or {}).get('latitude'),
                   "lon":(a.get('metadata') or {}).get('longitude')}
                  for a in (plans[0].get('activities') or [])][:3]
        print("  plans", len(plans), "stops", [len(p.get('activities') or []) for p in plans])
        print("  coords", coords)
        json.dump({"journey_id":JID,"plan_ids":[p['id'] for p in plans],
                   "selected_plan_id":plans[0]['id'],"coords":coords},
                  open("D:/moodle/_v1922_work/rc_evidence/be_chain.json","w",encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        json.dump(j, open("D:/moodle/_v1922_work/rc_evidence/journey.json","w",encoding="utf-8"),
                  ensure_ascii=False, indent=1)

json.dump({"journey_id":JID,"trace":TRACE},
          open("D:/moodle/_v1922_work/rc_evidence/be_trace.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("DONE" if len(ids)>=2 else "BLOCKED:not enough POIs")

"""T2 — no-op replans are forbidden for CLOSURE / WEATHER."""
import json, subprocess, sqlite3, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"

def call(method, path, body=None, timeout=300, hdrs=()):
    a = ["curl","-s","-X",method,B+path,"-H","Content-Type: application/json"]
    for h in hdrs: a += ["-H", h]
    if body is not None: a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw": r.stdout[:300]}

def mkjourney():
    tv = call("POST","/travelers",{"display_name":"厦门旅客","timezone":"Asia/Shanghai","locale":"zh-CN"})
    j = call("POST","/journeys",{
        "traveler_id":tv["id"],"title":"厦门三天","city_code":"CN-XIAMEN","timezone":"Asia/Shanghai",
        "start_at":"2026-11-06T10:00:00+08:00","end_at":"2026-11-08T20:00:00+08:00",
        "budget":{"amount_minor":300000,"currency":"CNY"},"stay_budget":{"amount_minor":100000,"currency":"CNY"},
        "party_size":2,"occupancy":{"adults":2,"rooms":1},
        "arrival_anchor":{"at":"2026-11-06T10:00:00+08:00","location":"厦门高崎国际机场"},
        "departure_anchor":{"at":"2026-11-08T20:00:00+08:00","location":"厦门北站"}})
    return j["id"]

def pois(JID):
    con = sqlite3.connect(DB)
    return [r[0] for r in con.execute(
        "select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]

JID = mkjourney()
for q in ["tourist attraction","restaurant","cafe","museum"]:
    if len(pois(JID)) >= 6: break
    call("POST",f"/journeys/{JID}/real-city/discover",{"query":q,"mode":"live","limit":6,"radius_m":5000})
ids = pois(JID)
gen = call("POST",f"/journeys/{JID}/plans/generate",{"place_ids":ids,"candidate_count":3})
plans = gen if isinstance(gen, list) else []
print("journey", JID, "| POIs", len(ids), "| plans", len(plans), flush=True)
if not plans: print("BLOCKED", json.dumps(gen,ensure_ascii=False)[:200]); raise SystemExit(2)
call("POST",f"/journeys/{JID}/plans/{plans[0]['id']}/select")
call("POST",f"/journeys/{JID}/start")

exp = call("GET",f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
mutable = [a for a in acts if a.get("type") == "visit" and not a.get("protected")]
print("mutable POIs:", len(mutable), flush=True)

# --- T2a: CLOSURE on a mutable real POI must yield a MATERIAL diff ---
target = mutable[0]
ev = call("POST",f"/journeys/{JID}/events",{
    "event_type":"CLOSURE","severity":"MAJOR","affected_activity_id":target["id"],"provenance":"USER_REPORTED"})
prop = call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":ev["id"]})
print("\n[T2a] target:", target.get("title"), flush=True)
if prop.get("id"):
    diff = prop.get("diff") or {}
    removed = diff.get("removed") or []
    added = diff.get("added") or []
    print(f"  proposal {prop['id'][:8]} status={prop.get('status')} family={prop.get('explanation',{}).get('family')}")
    print(f"  removed={len(removed)} added={len(added)}")
    print(f"  removed ids: {removed[:4]}")
    print(f"  added ids  : {[str(x)[:34] for x in added[:4]]}")
    material = bool(removed or added)
    print("  T2a:", "PASS (material change)" if material else "FAIL (NO-OP)")
else:
    print("  T2a: rejected ->", json.dumps(prop, ensure_ascii=False)[:200])

# --- T2b: CLOSURE on a protected stay node must NOT fake a repair ---
protected = [a for a in acts if a.get("type") in {"check_in","stay"} or a.get("protected")]
print("\n[T2b] protected candidates:", [(a.get("type"), a.get("protected")) for a in protected][:3], flush=True)
if protected:
    ev2 = call("POST",f"/journeys/{JID}/events",{
        "event_type":"CLOSURE","severity":"MAJOR","affected_activity_id":protected[0]["id"],"provenance":"USER_REPORTED"})
    prop2 = call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":ev2["id"]})
    if prop2.get("id"):
        d2 = prop2.get("diff") or {}
        print(f"  proposal {prop2['id'][:8]} removed={len(d2.get('removed') or [])} added={len(d2.get('added') or [])} family={prop2.get('explanation',{}).get('family')}")
        print("  T2b:", "FAIL (fake repair on protected)" if not (d2.get('removed') or d2.get('added')) else "PASS (material)")
    else:
        msg = (prop2.get("error") or {}).get("message") or ""
        code = (prop2.get("error") or {}).get("code") or ""
        ok = "PROTECTED" in msg.upper() or "NO_ALTERNATIVE" in msg.upper() or "UNRESOLVED" in msg.upper()
        print(f"  rejected code={code} msg={str(msg)[:120]}")
        print("  T2b:", "PASS (honest refusal)" if ok else "PARTIAL")

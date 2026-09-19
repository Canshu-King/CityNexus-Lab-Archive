"""Regenerate the T1 stay-preservation evidence on a clean DB."""
import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
OUT = "D:/moodle/_v1922_work/CityNexus-EAC-FinalConsumer-Truth- UX-Closure-20260916"
OUT = OUT.replace("- UX", "-UX")

def call(m,p,b=None,t=300):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}

tv = call("POST","/travelers",{"display_name":"厦门旅客","timezone":"Asia/Shanghai","locale":"zh-CN"})
j = call("POST","/journeys",{
  "traveler_id":tv["id"],"title":"厦门三天","city_code":"CN-XIAMEN","timezone":"Asia/Shanghai",
  "start_at":"2026-11-06T10:00:00+08:00","end_at":"2026-11-08T20:00:00+08:00",
  "budget":{"amount_minor":300000,"currency":"CNY"},"stay_budget":{"amount_minor":100000,"currency":"CNY"},
  "party_size":2,"occupancy":{"adults":2,"rooms":1},
  "arrival_anchor":{"at":"2026-11-06T10:00:00+08:00","location":"厦门高崎国际机场"},
  "departure_anchor":{"at":"2026-11-08T20:00:00+08:00","location":"厦门北站"}})
JID = j["id"]; print("JID", JID, flush=True)

def pois():
    con=sqlite3.connect(DB)
    return [r[0] for r in con.execute("select id from places where id like 'real-place-%' and city_code='CN-XIAMEN' order by id limit 6")]
import time
for attempt in range(6):
    if len(pois()) >= 6: break
    for q in ["tourist attraction","restaurant","cafe","museum","bar","park"]:
        if len(pois()) >= 6: break
        r = call("POST",f"/journeys/{JID}/real-city/discover",
                 {"query":q,"mode":"live","limit":6,"radius_m":5000})
        n = len(r.get("candidates") or []) if isinstance(r, dict) else 0
        print(f"  discover {q} -> {n}", flush=True)
        if n: break
    if len(pois()) < 6: time.sleep(5)
ids=pois(); print("POIs", len(ids), flush=True)
gen=call("POST",f"/journeys/{JID}/plans/generate",{"place_ids":ids,"candidate_count":3})
plans=gen if isinstance(gen,list) else []
print("plans",len(plans), flush=True)
if not plans: print("BLOCKED", json.dumps(gen,ensure_ascii=False)[:180]); raise SystemExit(2)
call("POST",f"/journeys/{JID}/plans/{plans[0]['id']}/select")
call("POST",f"/journeys/{JID}/start")

def snap():
    con=sqlite3.connect(DB)
    plan=con.execute("select active_plan_version_id from journeys where id=?",(JID,)).fetchone()[0]
    rows=list(con.execute("""select a.sequence_no,a.activity_type,a.title,a.start_at,a.end_at
        from activities a where a.plan_version_id=? order by a.sequence_no""",(plan,)))
    return plan, rows

plan_before, rows_before = snap()
print("BEFORE plan", plan_before[:8], "stops", len(rows_before), flush=True)

call("POST",f"/journeys/{JID}/stays/offers/capture")
stay=call("POST",f"/journeys/{JID}/stay-options/generate")
top=(stay.get("top_k") or [])
print("stay options", len(top), flush=True)
sel={}
if top:
    sel=call("POST",f"/journeys/{JID}/stay-options/{top[0]['id']}/select")
plan_after, rows_after = snap()

def counts(rows):
    return {"poi": sum(1 for r in rows if r[1]=="visit"),
            "stay": sum(1 for r in rows if r[1] in {"check_in","check_out","stay"}),
            "anchor": sum(1 for r in rows if r[1] in {"arrival","departure"})}
ev = {
  "journey_id": JID, "city_code": "CN-XIAMEN",
  "stay_selected": (sel.get("option") or {}).get("stay", {}).get("property_name"),
  "gate": sel.get("deterministic_feasibility"),
  "protected_commitments_preserved": sel.get("protected_commitments_preserved"),
  "before": {"plan_id": plan_before, "counts": counts(rows_before),
             "sequence": [{"seq":r[0],"type":r[1],"title":r[2],"start":r[3][11:16],"end":r[4][11:16]} for r in rows_before]},
  "after":  {"plan_id": plan_after, "counts": counts(rows_after),
             "sequence": [{"seq":r[0],"type":r[1],"title":r[2],"start":r[3][11:16],"end":r[4][11:16]} for r in rows_after]},
}
ev["verdict_T1"] = ("PASS" if ev["after"]["counts"]["poi"] >= 3
                    and ev["after"]["counts"]["stay"] >= 2
                    and ev["after"]["counts"]["anchor"] >= 2 else "FAIL")
open(f"{OUT}/evidence/T1_STAY_PRESERVATION_EVIDENCE.json","w",encoding="utf-8").write(
    json.dumps(ev, indent=1, ensure_ascii=False))
print("BEFORE", ev["before"]["counts"], "AFTER", ev["after"]["counts"])
print("T1:", ev["verdict_T1"], "| gate:", ev["gate"])

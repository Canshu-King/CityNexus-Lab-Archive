"""Regenerate the T2 no-op-replan evidence on the live Xiamen journey."""
import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
OUT = "D:/moodle/_v1922_work/CityNexus-EAC-FinalConsumer-Truth-UX-Closure-20260916"

def call(m,p,b=None,t=300):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}

con=sqlite3.connect(DB)
JID=con.execute("select id from journeys order by created_at desc limit 1").fetchone()[0]
exp=call("GET",f"/journeys/{JID}/experience")
acts=(exp.get("active_plan") or {}).get("activities") or []
mutable=[a for a in acts if a.get("type") in {"visit","activity"}]
protected=[a for a in acts if a.get("type") in {"check_in","stay","check_out"}]
ev={"journey_id":JID,"city_code":"CN-XIAMEN","cases":[]}

# A) mutable real POI closure must be material
if mutable:
    tgt=mutable[0]
    e=call("POST",f"/journeys/{JID}/events",{"event_type":"CLOSURE","severity":"MAJOR",
        "affected_activity_id":tgt["id"],"provenance":"USER_REPORTED"})
    pr=call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":e["id"]})
    if pr.get("id"):
        d=pr.get("diff") or {}
        rm, ad = d.get("removed") or [], d.get("added") or []
        ev["cases"].append({"case":"mutable_real_poi_closure","target":tgt.get("title"),
            "proposal_id":pr["id"],"status":pr.get("status"),
            "family":(pr.get("explanation") or {}).get("family"),
            "removed":len(rm),"added":len(ad),
            "verdict":"PASS" if (rm or ad) else "FAIL_NOOP"})
    else:
        err=pr.get("error") or {}
        ev["cases"].append({"case":"mutable_real_poi_closure","target":tgt.get("title"),
            "rejected_code":err.get("code"),"message":str(err.get("message"))[:160],
            "verdict":"REFUSED_HONESTLY"})

# B) protected stay closure must not be faked into a repair
if protected:
    tgt=protected[0]
    e=call("POST",f"/journeys/{JID}/events",{"event_type":"CLOSURE","severity":"MAJOR",
        "affected_activity_id":tgt["id"],"provenance":"USER_REPORTED"})
    pr=call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":e["id"]})
    if pr.get("id"):
        d=pr.get("diff") or {}
        rm, ad = d.get("removed") or [], d.get("added") or []
        ev["cases"].append({"case":"protected_stay_closure","target":tgt.get("title"),
            "proposal_id":pr["id"],"removed":len(rm),"added":len(ad),
            "family":(pr.get("explanation") or {}).get("family"),
            "verdict":"FAIL_FAKE_REPAIR" if not (rm or ad) else "PASS_MATERIAL"})
    else:
        err=pr.get("error") or {}
        msg=str(err.get("message") or "")
        ev["cases"].append({"case":"protected_stay_closure","target":tgt.get("title"),
            "rejected_code":err.get("code"),"message":msg[:160],
            "verdict":"PASS_HONEST_REFUSAL" if any(k in msg.upper() for k in
                ("NO_ALTERNATIVE","UNRESOLVED","PROTECTED","NO_DISTINCT_CANDIDATE")) else "PARTIAL"})

open(f"{OUT}/evidence/T2_NOOP_REPLAN_EVIDENCE.json","w",encoding="utf-8").write(
    json.dumps(ev, indent=1, ensure_ascii=False))
for c in ev["cases"]:
    print(f"  {c['case']:28s} {c['verdict']:22s} {str(c.get('removed',''))}/{str(c.get('added',''))} {c.get('message','')[:60]}")

"""B5 — close a mutable POI on the STAY-materialised plan and probe recovery."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
def call(m,p,b=None,t=180):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}
info = json.loads(open("D:/moodle/_v1922_work/fc_evidence/b5_stay.json","rb").read().decode("utf-8"))
JID = info["journey_id"]
exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
print("active plan stops:", len(acts))
for a in acts: print(f"   {a.get('sequence_no'):2d} {a.get('type'):11s} {a.get('title')[:30]}")
pois=[a for a in acts if a.get("type") in {"visit","activity"}]
if not pois:
    print("B5: no mutable POI on stay plan"); raise SystemExit(0)
tgt=pois[0]
ev=call("POST",f"/journeys/{JID}/events",{"event_type":"CLOSURE","severity":"MAJOR",
    "affected_activity_id":tgt["id"],"provenance":"USER_REPORTED"})
pr=call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":ev["id"]})
print("\nB5 probe on stay-materialised plan, target:", tgt.get("title"))
if pr.get("id"):
    d=pr.get("diff") or {}
    rm,ad=len(d.get("removed") or []),len(d.get("added") or [])
    print(f"  proposal {pr['id'][:8]} removed={rm} added={ad}")
    print("  B5:", "PASS (material replan)" if (rm or ad) else "FAIL (no-op)")
else:
    err=pr.get("error") or {}; msg=str(err.get("message") or "")
    print("  rejected:", err.get("code"), "|", msg[:160])
    ok = any(k in msg.upper() for k in ("NO_ALTERNATIVE","UNRESOLVED","PROTECTED"))
    print("  B5:", "PASS (explicit refusal)" if ok else "FAIL (mobility identity mismatch)")

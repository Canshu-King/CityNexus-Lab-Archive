import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
def call(m,p,b=None,t=180):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/b5_journey.json","rb").read().decode("utf-8"))["journey_id"]
print("JID", JID[:8], flush=True)
# 1) 选住宿
call("POST", f"/journeys/{JID}/stays/offers/capture")
stay = call("POST", f"/journeys/{JID}/stay-options/generate")
top = (stay.get("top_k") or []) if isinstance(stay, dict) else []
print("stay options:", len(top), flush=True)
sel = {}
if top:
    sel = call("POST", f"/journeys/{JID}/stay-options/{top[0]['id']}/select")
print("select ->", (sel.get("deterministic_feasibility") or (sel.get("error") or {}).get("message","?"))[:110], flush=True)
# 2) 当前计划
exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
print("active stops:", len(acts))
for a in acts: print(f"   {a.get('sequence_no'):2d} {a.get('type'):11s} {a.get('title')[:32]}")
# 3) 关掉一个可变 POI
pois=[a for a in acts if a.get("type") in {"visit","activity"}]
if not pois:
    print("B5: no mutable POI"); raise SystemExit(0)
tgt=pois[0]
ev=call("POST",f"/journeys/{JID}/events",{"event_type":"CLOSURE","severity":"MAJOR",
    "affected_activity_id":tgt["id"],"provenance":"USER_REPORTED"})
pr=call("POST",f"/journeys/{JID}/replans",{"trigger_event_id":ev["id"]})
print("\nB5 probe target:", tgt.get("title"))
if pr.get("id"):
    d=pr.get("diff") or {}
    rm,ad=len(d.get("removed") or []),len(d.get("added") or [])
    print(f"  proposal {pr['id'][:8]} removed={rm} added={ad}")
    print("  B5:", "PASS (material replan)" if (rm or ad) else "FAIL (no-op)")
else:
    err=pr.get("error") or {}; msg=str(err.get("message") or "")
    print("  rejected:", err.get("code"), "|", msg[:150])
    ok = any(k in msg.upper() for k in ("NO_ALTERNATIVE","UNRESOLVED","PROTECTED"))
    print("  B5:", "PASS (explicit refusal)" if ok else "FAIL (mobility identity mismatch)")

"""B5 probe — can a stay-materialised plan recover from a POI closure?"""
import json, subprocess, sqlite3, sys, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"

def call(m,p,b=None,t=120):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}

con = sqlite3.connect(DB)
row = con.execute("select id from journeys order by created_at desc limit 1").fetchone()
if not row:
    print("no journey in db"); raise SystemExit(0)
JID = row[0]
exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
print("journey", JID[:8], "| active stops", len(acts))
for a in acts:
    print(f"   {a.get('sequence_no'):2d} {a.get('type'):10s} {a.get('title')[:30]}")
pois = [a for a in acts if a.get("type") in {"visit","activity"}]
if not pois:
    print("\nB5: no mutable POI on this plan (stay-materialised?) -> cannot probe")
    raise SystemExit(0)
tgt = pois[0]
ev = call("POST", f"/journeys/{JID}/events", {"event_type":"CLOSURE","severity":"MAJOR",
    "affected_activity_id": tgt["id"], "provenance":"USER_REPORTED"})
pr = call("POST", f"/journeys/{JID}/replans", {"trigger_event_id": ev["id"]})
print("\nB5 probe on", tgt.get("title"))
if pr.get("id"):
    d = pr.get("diff") or {}
    print("  proposal", pr["id"][:8], "removed", len(d.get("removed") or []), "added", len(d.get("added") or []))
    print("  B5:", "PASS (material)" if (d.get("removed") or d.get("added")) else "FAIL (no-op)")
else:
    err = pr.get("error") or {}
    msg = str(err.get("message") or "")
    print("  rejected:", err.get("code"), msg[:140])
    print("  B5:", "PASS (explicit refusal)" if any(k in msg.upper() for k in
        ("NO_ALTERNATIVE","UNRESOLVED","PROTECTED")) else "FAIL (mobility identity mismatch)")

"""T2b — a protected stay/check-in closure must NOT be faked into a repair."""
import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
def call(m,p,b=None,t=300):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:300]}

JID = sys.argv[1]
exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
nodes = [a for a in acts if a.get("type") in {"arrival","departure","check_in","stay","check_out"}]
print("structural nodes:", [(a.get("type"), a.get("protected")) for a in nodes][:6], flush=True)
target = next((a for a in acts if a.get("type") in {"check_in","stay","check_out"}), None)
if target is None:
    print("T2b: SKIP (no stay node on this plan)"); raise SystemExit(0)
print("target:", target.get("type"), target.get("title"), flush=True)
ev = call("POST", f"/journeys/{JID}/events", {
    "event_type":"CLOSURE","severity":"MAJOR","affected_activity_id":target["id"],"provenance":"USER_REPORTED"})
prop = call("POST", f"/journeys/{JID}/replans", {"trigger_event_id":ev["id"]})
if prop.get("id"):
    d = prop.get("diff") or {}
    r, a = len(d.get("removed") or []), len(d.get("added") or [])
    print(f"  proposal {prop['id'][:8]} removed={r} added={a}")
    print("  T2b:", "FAIL (no-op accepted)" if not (r or a) else "PASS (material)")
else:
    err = prop.get("error") or {}
    print(f"  rejected code={err.get('code')} msg={str(err.get('message'))[:130]}")
    msg = str(err.get("message") or "").upper()
    print("  T2b:", "PASS (honest refusal)" if any(k in msg for k in ("PROTECTED","NO_ALTERNATIVE","UNRESOLVED")) else "PARTIAL")

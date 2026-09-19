import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
plans = get(f"/journeys/{J}/plans")
for p in plans:
    acts = p.get("activities") or []
    days = sorted({str(a.get("start_at") or "")[:10] for a in acts if a.get("start_at")})
    print(p["id"][:8], p.get("status"), "source=", p.get("source"), "mode=", p.get("planning_mode"),
          "acts=", len(acts), "days=", days)
    print("   version_no=", p.get("version_no"), "parent=", str(p.get("parent_plan_version_id"))[:8])

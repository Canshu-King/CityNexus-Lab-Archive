import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
def call(method, path, body=None, timeout=300):
    a = ["curl","-s","-X",method,B+path,"-H","Content-Type: application/json"]
    if body is not None: a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw": r.stdout[:400]}
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
exp = call("GET", f"/journeys/{JID}/experience")
opts = exp.get("options") or []
print("options:", len(opts))
for o in opts[:4]:
    print("  ", o.get("id","")[:8], o.get("status"), "|", (o.get("stay") or {}).get("property_name"),
          "| hard_pass", o.get("hard_constraints_passed"))
sel = [o for o in opts if o.get("status") == "SELECTED"]
print("selected:", [o.get("id","")[:8] for o in sel])
con = sqlite3.connect(DB)
print("\nmaterialization failures (last 6):")
for r in con.execute("select status, failure_reason, created_at from stay_journey_options order by created_at desc limit 6"):
    print("  ", r)
print("\nplan versions:")
for r in con.execute("select id, version_no, status, source from plan_versions where journey_id=? order by version_no", (JID,)):
    print("  ", r[0][:10], "v", r[1], r[2], r[3])

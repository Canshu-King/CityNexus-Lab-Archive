import json, subprocess, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
def call(m,p,b=None,t=300):
    a=["curl","-s","-X",m,B+p,"-H","Content-Type: application/json"]
    if b is not None: a+=["-d",json.dumps(b,ensure_ascii=False)]
    r=subprocess.run(a,capture_output=True,text=True,encoding="utf-8",timeout=t)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw":r.stdout[:400]}
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
exp = call("GET", f"/journeys/{JID}/experience")
opts = exp.get("options") or []
oid = opts[0]["id"]
print("selecting option", oid[:8], flush=True)
res = call("POST", f"/journeys/{JID}/stay-options/{oid}/select")
print(json.dumps(res, ensure_ascii=False)[:700])

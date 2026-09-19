import json, urllib.request, io, sys, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u): return json.loads(urllib.request.urlopen(B+u, timeout=120).read().decode("utf-8"))
def post(u, body):
    r=urllib.request.Request(B+u, data=json.dumps(body).encode(), headers={"Content-Type":"application/json","Idempotency-Key":str(uuid.uuid4())})
    try:
        return urllib.request.urlopen(r, timeout=300).read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return "HTTP %d %s" % (e.code, e.read().decode("utf-8")[:300])

exp = get(f"/journeys/{J}/experience")
acts = exp["active_plan"]["activities"]
tgt = [a for a in acts if not a.get("locked")][0]
print("target:", tgt["title"][:26])
ev = json.loads(post(f"/journeys/{J}/events", {"event_type":"CLOSURE","severity":"MAJOR","affected_activity_id":tgt["id"],"provenance":"USER_REPORTED"}))
print("event:", ev.get("id"))
print("replan:", post(f"/journeys/{J}/replans", {"trigger_event_id": ev["id"]})[:300])

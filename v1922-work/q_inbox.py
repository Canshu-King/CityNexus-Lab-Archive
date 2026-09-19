import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
d = get(f"/journeys/{J}/inbox")
print("journey", J)
print(json.dumps(d, ensure_ascii=False, indent=1)[:3000])

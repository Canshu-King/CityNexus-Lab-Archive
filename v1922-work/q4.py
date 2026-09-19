import json, urllib.request, io
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
print(type(so), (list(so.keys()) if isinstance(so, dict) else so[:3]))
if isinstance(so, dict):
    for k,v in so.items():
        print(k, type(v).__name__, (len(v) if isinstance(v,(list,dict)) else v))

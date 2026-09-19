import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
body = json.dumps({"query":"厦门 酒店","limit":10}).encode()
r = urllib.request.Request(f"{B}/journeys/{J}/stays/search", data=body, headers={"Content-Type":"application/json"})
try:
    d = json.loads(urllib.request.urlopen(r, timeout=300).read().decode("utf-8"))
    print("keys:", list(d.keys()) if isinstance(d, dict) else type(d))
    print(json.dumps(d, ensure_ascii=False)[:900])
except Exception as e:
    print("ERR", str(e)[:300])

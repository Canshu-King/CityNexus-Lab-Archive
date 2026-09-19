import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u): return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
opts = so["options"]
print("options:", len(opts))
for o in opts[:3]:
    r = urllib.request.Request(f"{B}/journeys/{J}/stay-options/{o['id']}/select", data=b"{}", headers={"Content-Type":"application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=120).read().decode("utf-8"))
        print("OK", o.get("property_name"), list(d.keys())[:5])
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode("utf-8")[:400])
    break
print("--- plan ---")
for a in so["active_plan"].get("activities") or []:
    print("  ", a.get("start_at"), "->", a.get("end_at"), "|", str(a.get("title"))[:30])

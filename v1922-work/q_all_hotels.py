import json, urllib.request, io, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u): return json.loads(urllib.request.urlopen(B+u, timeout=90).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
opts = so["options"]
print("journey", J, "options", len(opts))
for o in opts:
    r = urllib.request.Request(f"{B}/journeys/{J}/stay-options/{o['id']}/select", data=b"{}", headers={"Content-Type":"application/json"})
    try:
        urllib.request.urlopen(r, timeout=120).read()
        print("OK  ", o.get("property_name"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        msg = json.loads(body)["error"]["message"][:150] if body.startswith("{") else body[:150]
        print("FAIL", o.get("property_name"), "|", msg)

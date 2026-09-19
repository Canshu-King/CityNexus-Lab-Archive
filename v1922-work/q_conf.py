import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u): return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
print("journey", J, "| window", so["journey"]["start_at"], "->", so["journey"]["end_at"])
print("offers:")
for o in so["offers"]:
    print("  ", o.get("external_offer_id"), o.get("property_name"), "in", o.get("check_in_at"), "out", o.get("check_out_at"))
print("active plan activities:")
for a in so["active_plan"].get("activities") or []:
    print("  ", a.get("start_at"), "->", a.get("end_at"), "|", str(a.get("title"))[:32])

import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/chain_state.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
ap = so["active_plan"]
print("journey", J)
print("trip:", json.dumps(so["trip"], ensure_ascii=False)[:400])
print("--- active plan activities ---")
for a in ap.get("activities") or []:
    print(" ", a.get("start_at") or a.get("start_time"), "->", a.get("end_at") or a.get("end_time"),
          "|", str(a.get("type") or a.get("kind")), "|", str(a.get("title"))[:34], "| locked=", a.get("locked"), "| place=", str(a.get("place_id"))[:14])
print("--- options ---")
for o in so["options"]:
    print(" ", o.get("id","")[:8], o.get("status"), o.get("property_name"), o.get("conflict_code"), str(o.get("conflict_detail"))[:90])

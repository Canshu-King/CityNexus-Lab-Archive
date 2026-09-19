import json, urllib.request, io
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
print("stay-options:", len(so))
for o in so:
    print("  ", o.get("id")[:8], o.get("status"), o.get("selected"), o.get("property_name"), o.get("check_in_at"), o.get("check_out_at"), "conflict=", o.get("conflict_code"))
md = get(f"/journeys/{J}/multiday")
days = md.get("days") or []
print("days:", len(days))
for d in days:
    print(" DAY", d.get("date"), d.get("label"))
    for a in (d.get("activities") or d.get("stops") or []):
        print("   ", a.get("start_time"), a.get("end_time"), a.get("kind"), a.get("title"), "pinned=", a.get("pinned"))

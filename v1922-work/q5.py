import json, urllib.request, io
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=60).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
for o in so["options"]:
    print("OPT", o.get("id","")[:8], o.get("status"), "sel=", o.get("selected"), "|", o.get("property_name"),
          "| in", o.get("check_in_at"), "out", o.get("check_out_at"))
ap = so["active_plan"]
print("active_plan keys:", list(ap.keys()))
acts = ap.get("activities") or []
print("active activities:", len(acts))
for a in acts:
    print("   ", a.get("start_time"), a.get("end_time"), a.get("kind"), a.get("title"), "pinned=", a.get("pinned"), "locked=", a.get("locked"))

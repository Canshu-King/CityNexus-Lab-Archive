import json, urllib.request, io
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/run_canonical_partial.json", encoding="utf-8"))["journey_id"]
B="http://127.0.0.1:8000/api/v1"
def get(u):
    return json.loads(urllib.request.urlopen(B+u, timeout=40).read().decode("utf-8"))
print("journey", J)
j = get(f"/journeys/{J}")
print("city", j.get("city_code"), "| status", j.get("status"), "| title", j.get("title"))
plans = get(f"/journeys/{J}/plans")
print("plans", len(plans))
for p in plans:
    print("  ", p.get("status"), "selected=", p.get("selected"), p.get("title"))
md = get(f"/journeys/{J}/multiday")
if isinstance(md, dict):
    for k in ("days","timeline","summary"):
        if k in md:
            v = md[k]
            print("multiday", k, type(v).__name__, len(v) if isinstance(v,(list,dict)) else v)
    days = md.get("days") or []
    for d in days:
        print("  DAY", d.get("date"), len(d.get("activities") or d.get("stops") or []))
        for a in (d.get("activities") or d.get("stops") or []):
            print("     ", a.get("start_time"), a.get("end_time"), a.get("kind"), a.get("title"))

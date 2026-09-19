import json, urllib.request, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
J = json.load(io.open("D:/moodle/_v1922_work/o2_evidence/VISIBLE_UI_TRACE_FINAL.json", encoding="utf-8"))["journey_id"]
B = "http://127.0.0.1:8000/api/v1"
def get(u): return json.loads(urllib.request.urlopen(B + u, timeout=120).read().decode("utf-8"))
so = get(f"/journeys/{J}/stay-options")
print("journey", J)
print("window", so["journey"]["start_at"], "->", so["journey"]["end_at"])
o = so["offers"][0]
print("offer in", o.get("check_in_at"), "out", o.get("check_out_at"))
print("activities:")
for a in so["active_plan"]["activities"]:
    print("  ", a.get("start_at"), "->", a.get("end_at"), "|", str(a.get("title"))[:30], "| locked=", a.get("locked"))

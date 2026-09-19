"""Create the canonical Xiamen Journey through the same API the UI uses.

Never calls /demo/reset.  Prints the journey_id for the trace.
"""
import json, io, sys, subprocess, uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
def post(p, body):
    r = subprocess.run(["curl","-s","-X","POST",B+p,"-H","Content-Type: application/json",
                        "-d", json.dumps(body, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"raw": r.stdout[:300]}

traveler = post("/travelers", {"display_name": "厦门旅客", "timezone": "Asia/Shanghai", "locale": "zh-CN"})
print("traveler:", traveler.get("id"))
jid = None
body = {
  "traveler_id": traveler["id"],
  "title": "厦门三天",
  "city_code": "CN-XIAMEN",
  "timezone": "Asia/Shanghai",
  "start_at": "2026-11-06T10:00:00+08:00",
  "end_at": "2026-11-08T20:00:00+08:00",
  "budget": {"amount_minor": 300000, "currency": "CNY"},
  "stay_budget": {"amount_minor": 100000, "currency": "CNY"},
  "party_size": 2,
  "occupancy": {"adults": 2, "rooms": 1},
  "arrival_anchor": {"at": "2026-11-06T10:00:00+08:00", "location": "厦门高崎国际机场"},
  "departure_anchor": {"at": "2026-11-08T20:00:00+08:00", "location": "厦门北站"},
}
j = post("/journeys", body)
print("journey:", j.get("id"), "city:", j.get("city_code"), "status:", j.get("status"))
open("D:/moodle/_v1922_work/rc_evidence/journey.json","w",encoding="utf-8").write(json.dumps(j, ensure_ascii=False, indent=1))

"""Build an offline Xiamen journey with real POIs so B5 can be probed fast."""
import datetime as dt
import json
import sqlite3
import subprocess
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
TAG = uuid.uuid4().hex[:6]
NOW = "2026-09-16T00:00:00+00:00"
BASE = "2026-11-06T11:00:00+08:00"


def call(method, path, body=None, timeout=120):
    args = ["curl", "-s", "-X", method, B + path, "-H", "Content-Type: application/json"]
    if body is not None:
        args += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:300]}


traveler = call("POST", "/travelers", {
    "display_name": f"B5-{TAG}", "timezone": "Asia/Shanghai", "locale": "zh-CN"})
journey = call("POST", "/journeys", {
    "traveler_id": traveler["id"], "title": "厦门三天", "city_code": "CN-XIAMEN",
    "timezone": "Asia/Shanghai",
    "start_at": "2026-11-06T10:00:00+08:00", "end_at": "2026-11-08T20:00:00+08:00",
    "budget": {"amount_minor": 300000, "currency": "CNY"},
    "stay_budget": {"amount_minor": 100000, "currency": "CNY"},
    "party_size": 2, "occupancy": {"adults": 2, "rooms": 1},
    "arrival_anchor": {"at": "2026-11-06T10:00:00+08:00", "location": "厦门高崎国际机场"},
    "departure_anchor": {"at": "2026-11-08T20:00:00+08:00", "location": "厦门北站"}})
JID = journey["id"]

con = sqlite3.connect(DB, timeout=30)
plan_id = str(uuid.uuid4())
poi_ids = []
for index in range(4):
    pid = f"real-place-b5-{TAG}-{index}"
    poi_ids.append(pid)
    con.execute(
        "insert or replace into places (id,provider_key,external_id,city_code,name,"
        "category,latitude,longitude,opening_hours_json,tags_json,metadata_json,updated_at)"
        " values (?,?,?,?,?,?,?,?,?,?,?,?)",
        (pid, "overpass", f"node/{TAG}/{index}", "CN-XIAMEN", f"厦门景点{index}",
         "attraction", 24.4800 + index * 0.0008, 118.0900 + index * 0.0008,
         '{"status":"UNKNOWN"}', '["real_city"]', '{"cost_minor":0}', NOW))
con.execute(
    "insert or replace into plan_versions (id,journey_id,version_no,planning_mode,status,"
    "source,total_cost_minor,currency,score_breakdown_json,utility_score,"
    "estimated_duration_min,created_at) values (?,?,?,?,?,?,?,?,?,?,?,?)",
    (plan_id, JID, 1, "balanced", "ACTIVE", "INITIAL", 0, "CNY", "{}", 0.9, 540, NOW))
for index, pid in enumerate(poi_ids):
    start = dt.datetime.fromisoformat(BASE) + dt.timedelta(hours=index * 4)
    con.execute(
        "insert or replace into activities (id,plan_version_id,sequence_no,activity_type,"
        "title,place_id,city_service_id,start_at,end_at,travel_from_prev_min,"
        "estimated_cost_minor,currency,status,locked,metadata_json,created_at,updated_at)"
        " values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid5(uuid.NAMESPACE_URL, f"b5-{TAG}-{index}")), plan_id, index + 1,
         "visit", f"厦门景点{index}", pid, None, start.isoformat(),
         (start + dt.timedelta(hours=1)).isoformat(), 20, 0, "CNY", "PLANNED", 0,
         json.dumps({"semantic_key": pid, "role": "ACTIVITY"}), NOW, NOW))
con.execute("update journeys set active_plan_version_id=?, status='ACTIVE' where id=?",
            (plan_id, JID))
con.commit()
con.close()

print("JID", JID, "| plan", plan_id[:8], "| POIs", len(poi_ids))
with open("D:/moodle/_v1922_work/fc_evidence/b5_journey.json", "w", encoding="utf-8") as fh:
    json.dump({"journey_id": JID, "plan_id": plan_id, "poi_ids": poi_ids}, fh,
              ensure_ascii=False)

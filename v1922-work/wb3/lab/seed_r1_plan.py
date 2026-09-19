# Seed an ACTIVE plan with a current-position museum activity (isolated DB only)
# -*- coding: utf-8 -*-
import sqlite3, uuid
from datetime import datetime, timedelta, timezone

DB = r"D:\moodle\CityNexus-WorkBuddy\overnight-20260917\recheck_rt_be\backend\citynexus.db"
JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9"
PID = str(uuid.uuid4())
PLACE = "place-gulangyu-organ"
TITLE = "\u9f13\u6d6a\u5c7f\u98ce\u7434\u535a\u7269\u9986(\u4e34\u65f6\u5c55\u9986)"  # 榧撴氮灞块鐞村崥鐗╅(涓存椂灞曢)
now = datetime.now(timezone.utc).replace(microsecond=0)

c = sqlite3.connect(DB)
c.execute("""INSERT OR REPLACE INTO places (id, provider_key, external_id, city_code, name, category,
             latitude, longitude, opening_hours_json, tags_json, metadata_json, updated_at)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
          (PLACE, "osm", "osm-organ-test", "CN-XIAMEN", TITLE, "museum",
           24.4435, 118.0652, '{"open":"08:30","close":"17:00"}',
           '["culture"]', '{"duration_min":90,"cost_minor":0}', now.isoformat()))
c.execute("""INSERT OR REPLACE INTO plan_versions (id, journey_id, version_no, planning_mode, status, source,
             total_cost_minor, currency, estimated_duration_min, created_at)
             VALUES (?,?,?,?,?,?,?,?,?,?)""",
          (PID, JID, 1, "balanced", "ACTIVE", "INITIAL", 12000, "CNY", 480, now.isoformat()))
acts = [
    ("a1", 1, "ATTRACTION", "Gulangyu Pier Meetup", None, None,
     (now - timedelta(hours=3)).isoformat(), (now - timedelta(hours=2, minutes=40)).isoformat(), 0),
    ("a2", 2, "ATTRACTION", TITLE, PLACE, None,
     (now - timedelta(minutes=30)).isoformat(), (now + timedelta(minutes=90)).isoformat(), 15),
    ("a3", 3, "FOOD", "Longtou Road Lunch", None, None,
     (now + timedelta(hours=2)).isoformat(), (now + timedelta(hours=3, minutes=30)).isoformat(), 20),
]
for aid, seq, typ, title, pl, cs, s, e, tv in acts:
    c.execute("""INSERT INTO activities (id, plan_version_id, sequence_no, activity_type, title,
                 place_id, city_service_id, start_at, end_at, travel_from_prev_min,
                 estimated_cost_minor, currency, status, locked, metadata_json, created_at, updated_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (f"{PID[:8]}-{aid}", PID, seq, typ, title, pl, cs, s, e, tv,
               4000, "CNY", "PLANNED", 0, '{}', now.isoformat(), now.isoformat()))
c.execute("UPDATE journeys SET status='ACTIVE', active_plan_version_id=? WHERE id=?", (PID, JID))
c.commit()
print("seeded plan:", PID)
print("museum activity:", f"{PID[:8]}-a2", "place:", PLACE)
print("journey:", c.execute("select status, active_plan_version_id from journeys where id=?", (JID,)).fetchone())
c.close()

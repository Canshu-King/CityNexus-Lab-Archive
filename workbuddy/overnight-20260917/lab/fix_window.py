# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc).replace(microsecond=0)
c = sqlite3.connect(r"D:\moodle\CityNexus-WorkBuddy\overnight-20260917\recheck_rt_be\backend\citynexus.db")
c.execute("update journeys set start_at=?, end_at=? where id=?",
          ((now - timedelta(hours=8)).isoformat(), (now + timedelta(hours=40)).isoformat(),
           "841a1c79-249d-4844-95ed-647279acd603"))
h = '{"open":"00:00","close":"23:59"}'
for p in ("place-gulangyu-organ", "place-gulangyu-pier", "place-longtou-food"):
    c.execute("update places set opening_hours_json=? where id=?", (h, p))
c.commit()
print("window:", c.execute("select start_at, end_at from journeys where id=?",
                           ("841a1c79-249d-4844-95ed-647279acd603",)).fetchone())
print("hours fixed:", c.execute("select count(*) from places where opening_hours_json=?", (h,)).fetchone())
c.close()

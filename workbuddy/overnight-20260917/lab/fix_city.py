# -*- coding: utf-8 -*-
import sqlite3
c = sqlite3.connect(r"D:\moodle\CityNexus-WorkBuddy\overnight-20260917\recheck_rt_be\backend\citynexus.db")
for p in ("place-gulangyu-organ", "place-gulangyu-pier", "place-longtou-food"):
    c.execute("update places set city_code=(select city_code from journeys where id='841a1c79-249d-4844-95ed-647279acd603') where id=?", (p,))
c.commit()
for r in c.execute("select id, city_code from places where id like 'place-gulangyu%' or id like 'place-longtou%'").fetchall():
    print(r[0], repr(r[1]))
c.close()

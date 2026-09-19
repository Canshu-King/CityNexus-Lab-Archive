# -*- coding: utf-8 -*-
import sqlite3
c = sqlite3.connect(r"D:\moodle\CityNexus-WorkBuddy\overnight-20260917\recheck_rt_be\backend\citynexus.db")
print("journey city_code:", c.execute("select city_code from journeys where id='841a1c79-249d-4844-95ed-647279acd603'").fetchone())
for r in c.execute("select id, provider_key, city_code, category, metadata_json from places where id like 'place-gulangyu%' or id like 'place-longtou%'").fetchall():
    print(r)
c.close()

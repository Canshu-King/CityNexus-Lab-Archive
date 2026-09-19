import json, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
con = sqlite3.connect(DB)
print("mobility facts for POI pairs (WALK):")
for r in con.execute("""select from_key, to_key, mode, duration_min from mobility_facts
    where journey_id=? and mode='WALK' and from_key like 'real-place-%' order by from_key limit 12""", (JID,)):
    print(f"  {r[0][-24:]:26s} -> {r[1][-24:]:26s} {r[2]:6s} {r[3]} min")
print()
print("POI coords + scheduled times:")
for r in con.execute("""select a.sequence_no, a.title, a.start_at, a.end_at, p.latitude, p.longitude
    from activities a join places p on p.id=a.place_id
    where a.plan_version_id=(select active_plan_version_id from journeys where id=?) order by a.sequence_no""", (JID,)):
    print(f"  {r[0]} {r[2][11:16]}-{r[3][11:16]} {r[1][:22]:24s} {round(r[4],4)},{round(r[5],4)}")

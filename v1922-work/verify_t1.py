import json, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
con = sqlite3.connect(DB)
plan = con.execute("select active_plan_version_id from journeys where id=?", (JID,)).fetchone()[0]
print("FINAL plan", plan[:10])
rows = list(con.execute("""select a.sequence_no, a.activity_type, a.title, a.start_at, a.end_at, p.name
    from activities a left join places p on p.id=a.place_id
    where a.plan_version_id=? order by a.sequence_no""", (plan,)))
real, stay, anchor = 0, 0, 0
for r in rows:
    print(f"  {r[0]} {r[1]:12s} {r[3][11:16]}-{r[4][11:16]} {r[2][:38]}")
    if r[1] in {"visit", "activity"}: real += 1
    elif r[1] in {"check_in","check_out","stay"}: stay += 1
    else: anchor += 1
print()
print(f"POI(visit)={real}  stay nodes={stay}  anchors={anchor}")
print("T1:", "PASS - POIs preserved AND stay inserted" if real >= 3 and stay >= 2 else "FAIL")

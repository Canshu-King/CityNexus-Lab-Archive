import json, sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = "D:/moodle/_v1922_work/fc_evidence/_db/live.db"
JID = json.loads(open("D:/moodle/_v1922_work/fc_evidence/repro_t1.json","rb").read().decode("utf-8"))["journey_id"]
con = sqlite3.connect(DB)
plan = con.execute("select active_plan_version_id from journeys where id=?", (JID,)).fetchone()[0]
print("plan", plan[:10])
for r in con.execute("select sequence_no, activity_type, title, start_at, end_at from activities where plan_version_id=? order by sequence_no", (plan,)):
    print(f"  {r[0]} {r[1]:12s} {r[3][11:16]}-{r[4][11:16]} {r[2][:34]}")
print()
print("offer check-in/out:")
for r in con.execute("select property_name, check_in_at, check_out_at, external_offer_id from accommodation_offer_snapshots where journey_id=? limit 3", (JID,)):
    print("  ", r[0][:20], r[1][:16], r[2][:16], r[3])

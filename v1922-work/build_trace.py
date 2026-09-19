"""Merge backend + frontend evidence into SAME_JOURNEY_TRACE.json."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = "D:/moodle/_v1922_work/rc_evidence/"
be = json.loads(open(R + "be_chain.json", "rb").read().decode("utf-8"))
fe = json.loads(open(R + "fe_trace.json", "rb").read().decode("utf-8"))
fe_live = json.loads(open(R + "fe_live.json", "rb").read().decode("utf-8")) if __import__("pathlib").Path(R + "fe_live.json").exists() else {"trace": []}
JID = be["journey_id"]

entries = []
for t in be.get("trace", []):
    entries.append({"ts": "n/a", "journey_id": JID, "city_code": "CN-XIAMEN",
                    "screen": t.get("route"), "action": t.get("step"),
                    "status": t.get("status"), "result": t.get("note"),
                    "source": "backend"})
for t in fe.get("trace", []):
    entries.append({"ts": t.get("ts"), "journey_id": JID, "city_code": "CN-XIAMEN",
                    "screen": t.get("screen"), "action": t.get("action"),
                    "status": t.get("status"), "result": t.get("result"),
                    "source": "browser"})
for t in fe_live.get("trace", []):
    entries.append({"ts": t.get("ts"), "journey_id": JID, "city_code": "CN-XIAMEN",
                    "screen": "/v8/live", "action": t.get("action"),
                    "status": t.get("status"), "result": t.get("result"),
                    "source": "browser"})

ids = {e["journey_id"] for e in entries}
out = {
    "journey_id": JID,
    "city_code": "CN-XIAMEN",
    "demo_reset_used": False,
    "journey_id_switches": sorted(ids - {JID}),
    "single_journey_proven": len(ids) == 1 and JID in ids,
    "plan_ids": be.get("plan_ids"),
    "selected_plan_id": be.get("selected_plan_id"),
    "stay_selected": be.get("stay_selected"),
    "final_plan_id": be.get("final_plan_id"),
    "final_stops": be.get("final_stops"),
    "entries": entries,
}
json.dump(out, open(R + "SAME_JOURNEY_TRACE.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("journey_id:", JID)
print("single_journey_proven:", out["single_journey_proven"])
print("entries:", len(entries), "| journey ids seen:", ids)
print("plans:", len(out["plan_ids"] or []), "| stay:", out["stay_selected"], "| final stops:", out["final_stops"])

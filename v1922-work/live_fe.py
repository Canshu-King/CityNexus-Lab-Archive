"""Drive a fresh disruption on the SAME Xiamen journey for the UI replan test."""
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
CHAIN = "D:/moodle/_v1922_work/rc_evidence/be_chain.json"
chain = json.loads(open(CHAIN, "rb").read().decode("utf-8"))
JID = chain["journey_id"]


def call(method, path, body=None):
    a = ["curl", "-s", "-X", method, B + path, "-H", "Content-Type: application/json"]
    if body is not None:
        a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=240)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:300]}


exp = call("GET", f"/journeys/{JID}/experience")
acts = (exp.get("active_plan") or {}).get("activities") or []
interior = [a for a in acts if a.get("type") not in {"arrival", "departure"}]
if not interior:
    print("BLOCKED: no interior activity")
    raise SystemExit(2)
target = interior[0]
ev = call("POST", f"/journeys/{JID}/events", {
    "event_type": "CLOSURE", "severity": "MAJOR",
    "affected_activity_id": target["id"], "provenance": "USER_REPORTED"})
print("event:", (ev.get("id") or "ERR")[:8], "target:", target.get("title"))
prop = call("POST", f"/journeys/{JID}/replans", {"trigger_event_id": ev["id"]})
msg = prop.get("id") or (prop.get("error") or {}).get("message") or "ERR"
print("proposal:", str(msg)[:80], "| status:", prop.get("status"),
      "| preserved:", prop.get("locked_commitments_preserved"))
chain["ui_event_id"] = ev.get("id")
chain["ui_proposal_id"] = prop.get("id")
json.dump(chain, open(CHAIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK" if prop.get("id") else "BLOCKED")

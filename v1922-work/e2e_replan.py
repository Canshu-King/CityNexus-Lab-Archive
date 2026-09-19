"""Live disruption -> governed replan on the SAME Xiamen journey."""
import json, io, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8000/api/v1"
state = json.load(open("D:/moodle/_v1922_work/rc_evidence/be_chain.json", encoding="utf-8"))
JID = state["journey_id"]
T = []

def call(method, path, body=None, timeout=240, hdrs=()):
    a = ["curl","-s","-X",method,B+path,"-H","Content-Type: application/json"]
    for h in hdrs: a += ["-H", h]
    if body is not None: a += ["-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    try: return json.loads(r.stdout)
    except Exception: return {"_raw": r.stdout[:300]}

def tr(step, route, resp, note=""):
    st = resp.get("error",{}).get("code") if isinstance(resp,dict) and "error" in resp else "OK"
    T.append({"step":step,"route":route,"status":st,"note":str(note)[:120]})

exp = call("GET", f"/journeys/{JID}/experience")
plan = exp.get("active_plan") or {}
acts = plan.get("activities") or []
tr("state", f"/journeys/{JID}/experience", exp, f"plan={plan.get('id','')[:8]} stops={len(acts)}")
print("active plan", plan.get("id"), "stops", len(acts), flush=True)
if not acts:
    print("BLOCKED: no active plan"); raise SystemExit(2)

# Pick a mid-trip activity to disrupt (skip first/last so a replan has room)
# Disrupt the first interior stop that is neither the arrival nor the
# departure anchor, which is what a real "the museum is closed" event looks
# like on the traveller's plan.
interior = [a for a in acts if a.get("type") not in {"arrival", "departure"}]
target = interior[0] if interior else acts[0]
tr("target", "activity", target, f"{target.get('title')} at {target.get('place_id')}")
print("target:", target.get("title"), target.get("place_id"), flush=True)

# 1) raise a CLOSURE event against that activity
ev = call("POST", f"/journeys/{JID}/events", {
    "event_type": "CLOSURE", "severity": "MAJOR",
    "affected_activity_id": target["id"], "provenance": "USER_REPORTED",
})
tr("event", "/events", ev, f"id={(ev.get('id') or '')[:8]} type=CLOSURE")
print("event:", (ev.get("id") or "ERR"), flush=True)
if not ev.get("id"):
    print("BLOCKED: event rejected", json.dumps(ev, ensure_ascii=False)[:200]); raise SystemExit(2)

# 2) governed replan proposal
prop = call("POST", f"/journeys/{JID}/replans", {"trigger_event_id": ev["id"]},
            hdrs=(f"Idempotency-Key: xiamen-replan-{ev['id'][:8]}",))
tr("replan", "/replans", prop, f"id={(prop.get('id') or '')[:8]} preserved={prop.get('locked_commitments_preserved')}")
print("proposal:", (prop.get("id") or "ERR"), "preserved:", prop.get("locked_commitments_preserved"), flush=True)
if not prop.get("id"):
    print("BLOCKED: no proposal", json.dumps(prop, ensure_ascii=False)[:220]); raise SystemExit(2)

# 3) traveller-visible proposal
shown = call("GET", f"/replans/{prop['id']}")
diff = shown.get("diff") or {}
tr("proposal-view", f"/replans/{prop['id'][:8]}", shown,
   f"removed={len(diff.get('removed') or [])} added={len(diff.get('added') or [])}")

# 4) accept -> authoritative state change
acc = call("POST", f"/replans/{prop['id']}/accept", None,
           hdrs=(f"Idempotency-Key: xiamen-accept-{prop['id'][:8]}",))
tr("accept", f"/replans/{prop['id'][:8]}/accept", acc, f"status={(acc.get('proposal') or {}).get('status')}")
print("accept:", (acc.get("proposal") or {}).get("status"), flush=True)

# 5) final consistent state
final = call("GET", f"/journeys/{JID}/experience")
fp = final.get("active_plan") or {}
rec = final.get("recovery")
flags = final.get("experience_flags") or {}
tr("final", f"/journeys/{JID}/experience", final,
   f"plan={fp.get('id','')[:8]} recovery={(rec or {}).get('state')} needs_review={flags.get('needs_review')}")
print("final plan:", fp.get("id"), "stops", len(fp.get("activities") or []))
print("recovery:", (rec or {}).get("state"), "needs_review:", flags.get("needs_review"))

state.update({
  "event_id": ev.get("id"), "proposal_id": prop.get("id"),
  "proposal_status": (acc.get("proposal") or {}).get("status"),
  "final_plan_id": fp.get("id"),
  "final_stops": len(fp.get("activities") or []),
  "diff_removed": diff.get("removed"), "diff_added": diff.get("added"),
  "replan_trace": T,
})
json.dump(state, open("D:/moodle/_v1922_work/rc_evidence/be_chain.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("OK")

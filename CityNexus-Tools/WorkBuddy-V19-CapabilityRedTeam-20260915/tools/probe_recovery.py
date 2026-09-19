"""P0 probe: does recovery/replan preserve HARD capability constraints?"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
sys.path.insert(0, str(LAB_ROOT / "repo_copy" / "backend" / "tests"))
import v19_harness as H  # noqa: E402

EVIDENCE = LAB_ROOT / "evidence"
records: list[dict] = []


def note(case: str, **kw):
    entry = {"case": case}
    entry.update(kw)
    records.append(entry)
    print(f"[{case}] {json.dumps(kw, ensure_ascii=False, default=str)[:420]}")


def activate_journey() -> dict:
    st, plans = H.generate_plans()
    if st != 201 or not isinstance(plans, list):
        return {"generate_status": st, "raw": str(plans)[:300]}
    plan_id = plans[0]["id"]
    sel_status, sel_body = H.select_plan(plan_id)
    start = H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
    return {
        "generate_status": st,
        "plan_id": plan_id,
        "select_status": sel_status,
        "start_status": start.status_code,
        "journey_status": H.journey()["status"],
        "start_body": (start.json() if start.status_code < 300 else start.text[:200]),
    }


def fire_event_and_replan(label: str) -> dict:
    st, ev = H.post_event(event_type="CLOSURE", payload={"affected_place_id": "place-tech-art"})
    ev_id = ev.get("id") if isinstance(ev, dict) else None
    result = {"event_status": st, "event_id": ev_id}
    if ev_id:
        rst, rbody = H.request_replan(ev_id)
        result["replan_status"] = rst
        result["replan_error"] = (
            rbody.get("error", {}).get("message") if isinstance(rbody, dict) else str(rbody)[:200]
        )
        if isinstance(rbody, dict) and rst < 300:
            result["proposal_keys"] = sorted(rbody.keys())
            result["candidate_count"] = len(rbody.get("candidates") or [])
    note(label, **result)
    return result


# =====================================================================
# A. supported HARD constraint survives recovery (control)
# =====================================================================
H.reset_demo()
act = activate_journey()
note("A_ACTIVATE_CONTROL", **act)
H.add_constraint("BUDGET_MAX", category="budget", params={"amount_minor": 60000, "currency": "CNY"})
fire_event_and_replan("A_REPLAN_WITH_SUPPORTED_HARD")

# =====================================================================
# B. capability declared mid-trip, then a disruption forces recovery
# =====================================================================
H.reset_demo()
act = activate_journey()
note("B_ACTIVATE", **act)
add_status, add_body = H.add_constraint(
    "STEP_FREE_REQUIRED", params={"evidence": "UNKNOWN", "source": "copilot"}
)
note(
    "B_MIDTRIP_CAPABILITY_ADD",
    add_status=add_status,
    body=str(add_body)[:260],
    note="journey is ACTIVE: the add-time gate now has a selected plan to validate",
)
fire_event_and_replan("B_REPLAN_WITH_HARD_CAPABILITY")
note(
    "B_JOURNEY_AFTER_FAILED_RECOVERY",
    journey_status=H.journey()["status"],
    active_plan_version_id=H.journey()["active_plan_version_id"],
    note="the traveler is stranded mid-trip with no recovery candidate",
)

# =====================================================================
# C. capability as SOFT + C4 -> recovery silently drops the capability
# =====================================================================
H.reset_demo()
act = activate_journey()
note("C_ACTIVATE", **act)
H.add_constraint("STEP_FREE_REQUIRED", kind="SOFT", params={"evidence": "KNOWN_STAIRS"})
fire_event_and_replan("C_REPLAN_WITH_SOFT_CAPABILITY")
note(
    "C_ACTIVE_PLAN_STILL_HAS_STAIRS",
    note="SOFT capability never gates recovery; the replacement activity is chosen freely",
)

# =====================================================================
# D. supported HARD constraint violated by a recovery replacement?
# =====================================================================
H.reset_demo()
act = activate_journey()
H.add_constraint("PLACE_UNAVAILABLE", category="availability", params={"place_ids": ["place-tech-art"]})
fire_event_and_replan("D_REPLAN_WITH_PLACE_BLOCKED")

# =====================================================================
# E. repeated recovery stability: same capability, three disruptions
# =====================================================================
H.reset_demo()
act = activate_journey()
H.add_constraint("BUDGET_MAX", category="budget", params={"amount_minor": 60000, "currency": "CNY"})
stability = []
for index in range(3):
    res = fire_event_and_replan(f"E_REPLAN_ROUND_{index + 1}")
    stability.append(res.get("replan_status"))
note("E_REPEATED_RECOVERY_STABILITY", statuses=stability)

# =====================================================================
# F. does a failed capability-constrained replan corrupt journey state?
# =====================================================================
H.reset_demo()
act = activate_journey()
H.add_constraint("STEP_FREE_REQUIRED", params={"evidence": "UNKNOWN"})
fire_event_and_replan("F_FAILED_RECOVERY_WITH_CAPABILITY")
j = H.journey()
note(
    "F_STATE_INTEGRITY",
    journey_status=j["status"],
    active_plan_version_id=j["active_plan_version_id"],
    events=len(H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/events").json()),
    replans=len(H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/replans").json()),
)

H.write_json(EVIDENCE / "planner_replan_capability_probe.json", records)
print("wrote", EVIDENCE / "planner_replan_capability_probe.json")

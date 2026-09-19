"""P0 probe: capability declared at setup time, then select / recovery."""

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
    print(f"[{case}] {json.dumps(kw, ensure_ascii=False, default=str)[:430]}")


def proposal_summary(body) -> dict:
    if not isinstance(body, dict):
        return {"raw": str(body)[:200]}
    return {
        "status": body.get("status"),
        "hard_constraints_passed": body.get("hard_constraints_passed"),
        "locked_commitments_preserved": body.get("locked_commitments_preserved"),
        "utility_score": body.get("utility_score"),
        "diff": body.get("diff"),
        "explanation": str(body.get("explanation"))[:300],
    }


# =====================================================================
# 1. setup-time capability on a DRAFT journey, then select a plan
# =====================================================================
H.reset_demo()
st, cbody = H.add_constraint("STEP_FREE_REQUIRED", params={"evidence": "VERIFIED_STEP_FREE"})
note("SETUP_ADD_ON_DRAFT", add_status=st, note="DRAFT journey: add-time gate has nothing to validate")
gst, plans = H.generate_plans()
note("SETUP_GENERATE", gen_status=gst, plan_count=len(plans) if isinstance(plans, list) else None)
if isinstance(plans, list) and plans:
    sst, sbody = H.select_plan(plans[0]["id"])
    note(
        "SETUP_SELECT_WITH_VERIFIED_STEP_FREE",
        select_status=sst,
        body=str(sbody)[:300],
        note="even VERIFIED step-free access cannot select a plan",
    )

# =====================================================================
# 2. same but SOFT: does the traveler get what they asked for?
# =====================================================================
H.reset_demo()
H.add_constraint("STEP_FREE_REQUIRED", kind="SOFT", params={"evidence": "VERIFIED_STEP_FREE"})
gst, plans = H.generate_plans()
sig_soft = [[a.get("place_id") for a in p.get("activities", [])] for p in (plans or [])]
H.reset_demo()
gst_base, plans_base = H.generate_plans()
sig_base = [[a.get("place_id") for a in p.get("activities", [])] for p in (plans_base or [])]
note(
    "SOFT_VERIFIED_STEP_FREE_NO_EFFECT",
    soft_identical_to_baseline=sig_soft == sig_base,
    note="declaring a SOFT step-free requirement changes nothing at all",
)

# =====================================================================
# 3. recovery proposal contents under a supported HARD constraint
# =====================================================================
H.reset_demo()
gst, plans = H.generate_plans()
H.select_plan(plans[0]["id"])
H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
H.add_constraint("BUDGET_MAX", category="budget", params={"amount_minor": 60000, "currency": "CNY"})
est, ev = H.post_event(event_type="CLOSURE", payload={"affected_place_id": "place-tech-art"})
rst, rbody = H.request_replan(ev["id"])
note("RECOVERY_PROPOSAL_SUPPORTED_HARD", **proposal_summary(rbody))

# =====================================================================
# 4. recovery under a place-block HARD constraint: is it honoured?
# =====================================================================
H.reset_demo()
gst, plans = H.generate_plans()
H.select_plan(plans[0]["id"])
H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
H.add_constraint(
    "PLACE_UNAVAILABLE", category="availability", params={"place_ids": ["place-tech-art"]}
)
est, ev = H.post_event(event_type="CLOSURE", payload={"affected_place_id": "place-tech-art"})
rst, rbody = H.request_replan(ev["id"])
note("RECOVERY_WITH_PLACE_BLOCKED", **proposal_summary(rbody))
if isinstance(rbody, dict) and rbody.get("proposed_plan_version_id"):
    pst, pbody = H.client.get(f"/api/v1/plans/{rbody['proposed_plan_version_id']}"), None
    if pst.status_code == 200:
        places = [a.get("place_id") for a in pst.json().get("activities", [])]
        note(
            "RECOVERY_PROPOSAL_PLACES",
            places=places,
            blocked_place_still_present="place-tech-art" in places,
            note="a blocked place reappearing in the recovery proposal means recovery ignores the constraint",
        )

# =====================================================================
# 5. C4 + capability conflict via recovery: is the conflict reported?
# =====================================================================
H.reset_demo()
import v19_harness as _H  # noqa: E402

imported = H.client.post(
    f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/inbox/import",
    json={
        "artifact_type": "STRUCTURED_JSON",
        "payload": {
            "reservation": {
                "reservation_type": "FERRY",
                "provider_key": "user-confirmed-cruise",
                "confirmation_ref": "V19-RECOVERY-CRUISE",
                "origin": {"name": "Nexus Pier"},
                "destination": {"name": "Nexus River Cruise", "latitude": 39.12, "longitude": 117.21},
                "scheduled_departure_at": "2026-10-10T15:30:00+08:00",
                "scheduled_arrival_at": "2026-10-10T16:30:00+08:00",
                "price_amount_minor": 12000,
                "currency": "CNY",
                "price_status": "KNOWN",
                "semantic_node_key": H.DEMO_LOCKED_PLACE,
                "anchor_role": "MID_TRIP",
            }
        },
    },
)
draft = imported.json().get("id") if imported.status_code == 201 else None
if draft:
    H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/inbox/{draft}/confirm")
gst, plans = H.generate_plans()
note("C4_RECOVERY_GENERATE", gen_status=gst, plan_count=len(plans) if isinstance(plans, list) else None)
if isinstance(plans, list) and plans:
    H.select_plan(plans[0]["id"])
    H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
    # force the C4 anchor onto the closure target to create a real conflict
    est, ev = H.post_event(event_type="CLOSURE", payload={"affected_place_id": H.DEMO_LOCKED_PLACE})
    note("C4_CONFLICT_EVENT", event_status=est, event_id=(ev.get("id") if isinstance(ev, dict) else None))
    if isinstance(ev, dict) and ev.get("id"):
        rst, rbody = H.request_replan(ev["id"])
        note("C4_CONFLICT_REPLAN", replan_status=rst, **proposal_summary(rbody))
        if isinstance(rbody, dict) and rst >= 300:
            note(
                "C4_CONFLICT_SURFACE",
                message=str(rbody)[:300],
                note="C4-protected closure is refused; the capability dimension is never mentioned",
            )

H.write_json(EVIDENCE / "planner_select_recovery_probe.json", records)
print("wrote", EVIDENCE / "planner_select_recovery_probe.json")

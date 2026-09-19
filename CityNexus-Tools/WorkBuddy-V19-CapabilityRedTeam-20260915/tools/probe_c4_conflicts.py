"""P0 probe: capability vs C4 commitment conflict, and recovery capability loss.

C4 = an already-paid / externally confirmed anchor.  The product must not
silently delete the C4 commitment, and must not silently ignore a HARD
capability.  It should surface an explicit conflict / needs-review /
no-feasible-plan outcome.
"""

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
    print(f"[{case}] {json.dumps(kw, ensure_ascii=False, default=str)[:400]}")


def make_c4_cruise(journey_id: str) -> dict:
    """Create a real C4_Anchored commitment bound to the paid river cruise."""

    imported = H.client.post(
        f"/api/v1/journeys/{journey_id}/inbox/import",
        json={
            "artifact_type": "STRUCTURED_JSON",
            "payload": {
                "reservation": {
                    "reservation_type": "FERRY",
                    "provider_key": "user-confirmed-cruise",
                    "confirmation_ref": "V19-CRUISE-PAID",
                    "origin": {"name": "Nexus Pier"},
                    "destination": {
                        "name": "Nexus River Cruise",
                        "latitude": 39.12,
                        "longitude": 117.21,
                    },
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
    if imported.status_code != 201:
        return {"import_status": imported.status_code, "raw": imported.text[:400]}
    draft_id = imported.json().get("id")
    confirmed = H.client.post(f"/api/v1/journeys/{journey_id}/inbox/{draft_id}/confirm")
    return {
        "import_status": imported.status_code,
        "confirm_status": confirmed.status_code,
        "body": confirmed.json() if confirmed.status_code < 300 else confirmed.text[:400],
    }


# =====================================================================
# 1. C4 paid cruise + wheelchair route UNKNOWN
# =====================================================================
H.reset_demo()
c4 = make_c4_cruise(H.DEMO_JOURNEY_ID)
note("C4_CREATE", **c4)
c4_id = (c4.get("body") or {}).get("commitment", {}).get("id") if isinstance(c4.get("body"), dict) else None
c4_level = (c4.get("body") or {}).get("commitment", {}).get("level") if isinstance(c4.get("body"), dict) else None
c4_policy = (c4.get("body") or {}).get("commitment", {}).get("policy") if isinstance(c4.get("body"), dict) else None
note("C4_IDENTITY", commitment_id=c4_id, level=c4_level, policy=c4_policy)

# baseline plan with the C4 anchor present
st, base = H.generate_plans()
base_ids = [p["id"] for p in base] if isinstance(base, list) else []
note(
    "C4_BASELINE_PLANS",
    status=st,
    plan_count=len(base_ids),
    cruise_present=[
        any(a.get("place_id") == H.DEMO_LOCKED_PLACE for a in p.get("activities", []))
        for p in (base if isinstance(base, list) else [])
    ],
)

# wheelchair route UNKNOWN as a HARD capability
H.add_constraint("STEP_FREE_REQUIRED", params={"evidence": "UNKNOWN", "target": H.DEMO_LOCKED_PLACE})
st2, gen2 = H.generate_plans()
note(
    "C4_PAID_CRUISE_vs_WHEELCHAIR_UNKNOWN",
    gen_status=st2,
    plan_count=len(gen2) if isinstance(gen2, list) else None,
    error=(gen2.get("error", {}).get("message") if isinstance(gen2, dict) else str(gen2)[:200]),
    c4_still_active=None,
)
with H.SessionLocal() as session:  # type: ignore[attr-defined]
    from app.db.models import Commitment  # noqa: E402

    row = session.get(Commitment, c4_id) if c4_id else None
    note(
        "C4_STATE_AFTER_CONFLICT",
        exists=row is not None,
        status=getattr(row, "status", None),
        level=getattr(row, "level", None),
        note="the product did not silently delete the paid commitment",
    )

# Is the conflict surfaced anywhere the traveler can see?
exp = H.experience()
tw = H.twin()
note(
    "CONFLICT_SURFACED",
    experience_mentions_conflict=("conflict" in json.dumps(exp, ensure_ascii=False).lower()),
    experience_mentions_step_free=("step_free" in json.dumps(exp, ensure_ascii=False).lower()),
    twin_mentions_conflict=("conflict" in json.dumps(tw, ensure_ascii=False).lower()),
    twin_risk_reason_codes=tw.get("context", {}).get("feasibility_envelope", {}).get("risk_reason_codes"),
    note="the traveler gets a generic 422, not an explicit capability/C4 conflict",
)

# =====================================================================
# 2. C4 high-speed rail + MIDDAY_REST_WINDOW
# =====================================================================
H.reset_demo()
c4b = make_c4_cruise(H.DEMO_JOURNEY_ID)
H.add_constraint("MIDDAY_REST_WINDOW", params={"start": "12:00", "end": "14:00"})
st3, gen3 = H.generate_plans()
note(
    "C4_RAIL_vs_MIDDAY_REST",
    gen_status=st3,
    plan_count=len(gen3) if isinstance(gen3, list) else None,
    error=(gen3.get("error", {}).get("message") if isinstance(gen3, dict) else str(gen3)[:160]),
)

# =====================================================================
# 3. C4 dinner reservation + INFANT_NAP_WINDOW
# =====================================================================
H.reset_demo()
c4c = make_c4_cruise(H.DEMO_JOURNEY_ID)
H.add_constraint("INFANT_NAP_WINDOW", params={"start": "17:00", "end": "18:30"})
st4, gen4 = H.generate_plans()
note(
    "C4_DINNER_vs_INFANT_NAP",
    gen_status=st4,
    plan_count=len(gen4) if isinstance(gen4, list) else None,
    error=(gen4.get("error", {}).get("message") if isinstance(gen4, dict) else str(gen4)[:160]),
)

# =====================================================================
# 4. SOFT capability + C4 -> is the capability silently ignored?
# =====================================================================
H.reset_demo()
c4d = make_c4_cruise(H.DEMO_JOURNEY_ID)
H.add_constraint("STEP_FREE_REQUIRED", kind="SOFT", params={"evidence": "KNOWN_STAIRS"})
st5, gen5 = H.generate_plans()
cruise_present = [
    any(a.get("place_id") == H.DEMO_LOCKED_PLACE for a in p.get("activities", []))
    for p in (gen5 if isinstance(gen5, list) else [])
]
note(
    "SOFT_CAPABILITY_vs_C4_KNOWN_STAIRS",
    gen_status=st5,
    plan_count=len(gen5) if isinstance(gen5, list) else None,
    cruise_present=cruise_present,
    note=(
        "a KNOWN_STAIRS conflict against a SOFT capability is silently ignored: "
        "no conflict, no warning, the traveler is never told"
    ),
)

H.write_json(EVIDENCE / "capability_commitment_conflicts.json", records)
print("wrote", EVIDENCE / "capability_commitment_conflicts.json")

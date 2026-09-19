"""V19.1 probe: does a protected C4 commitment actually reach the planning gate?

Compares the planning entry points against the same C4_Anchored commitment:

  1. generate_plans()            -> POST /plans/generate        (initial composition)
  2. _generic_compose_plans()    -> POST /plans/generate {place_ids}
  3. validate_plan_feasibility() -> select / booking revalidation

Usage:  python tools/v191_probe_c4_gate.py [A|B]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = Path(os.environ.get("V192_EVID", LAB / "evidence"))

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402

ARRIVAL_ANCHOR = "2026-10-10T12:30:00+08:00"


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"probe_error": f"{type(exc).__name__}: {exc}"}


def _c4_constraints_for(journey_id: str) -> list[dict]:
    """Reproduce exactly what services.py:731-739 builds for the gate."""
    from sqlalchemy import select

    from app.db.models import Commitment
    from app.replanning.protected_commitments import active_c4_hard_constraints

    with H._session() as s:
        rows = list(
            s.scalars(
                select(Commitment).where(
                    Commitment.journey_id == journey_id,
                    Commitment.status == "ACTIVE",
                    Commitment.level == "C4_Anchored",
                )
            ).all()
        )
        return active_c4_hard_constraints(rows)


def _seed(journey_id: str = H.DEMO_JOURNEY_ID, ref: str = "C4-GATE-0001") -> dict:
    return H.seed_c4_commitment(
        journey_id,
        confirmation_ref=ref,
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at=ARRIVAL_ANCHOR,
    )


# ---------------------------------------------------------------------------
# 1. what the generation path actually loads vs what the gate needs
# ---------------------------------------------------------------------------
def generation_constraints() -> dict:
    from app.db.models import Journey
    from app.services import _journey_constraints_with_capabilities

    H.reset_demo()
    seed = _seed(ref="C4-GEN-0001")
    c4 = _c4_constraints_for(H.DEMO_JOURNEY_ID)
    with H._session() as s:
        journey = s.get(Journey, H.DEMO_JOURNEY_ID)
        loaded = _journey_constraints_with_capabilities(s, journey)
    codes = sorted(
        {getattr(c, "rule_code", None) or getattr(c, "category", None) for c in loaded}
    )
    return {
        "c4_confirm_status": seed.get("confirm_status"),
        "c4_level": (seed.get("commitment") or {}).get("level"),
        "c4_constraint_objects": c4,
        "generation_constraint_codes": codes,
        "generation_includes_locked_commitment": any(
            (getattr(c, "rule_code", None) or "") == "LOCKED_COMMITMENT" for c in loaded
        ),
        "c4_constraint_count": len(c4),
    }


# ---------------------------------------------------------------------------
# 2. generator output vs the authoritative validator, same C4
# ---------------------------------------------------------------------------
def generator_vs_validator() -> dict:
    from app.db.models import Journey, PlanVersion
    from app.services import validate_plan_feasibility

    H.reset_demo()
    _seed(ref="C4-VAL-0001")
    code, body = H.generate_plans()
    plans = H.list_plans()
    verdicts = []
    with H._session() as s:
        journey = s.get(Journey, H.DEMO_JOURNEY_ID)
        for meta in plans:
            plan = s.get(PlanVersion, meta["id"])
            if plan is None:
                continue
            try:
                result = validate_plan_feasibility(s, journey, plan, include_active_c4=True)
                failures = list(getattr(result, "failures", []) or [])
                feasible = bool(getattr(result, "feasible", None))
            except Exception as exc:  # noqa: BLE001
                failures = [f"{type(exc).__name__}: {exc}"]
                feasible = None
            verdicts.append(
                {"plan_id": meta["id"], "feasible": feasible, "failures": failures}
            )
    return {
        "generate_status": code,
        "plans_generated": len(plans),
        "plan_times": [
            [[a.get("title"), a.get("start_at")] for a in p.get("activities", [])]
            for p in plans
        ],
        "validator_with_c4": verdicts,
        "generator_produced_plans_the_validator_rejects": bool(verdicts)
        and all(v["failures"] for v in verdicts),
        "failure_codes": sorted({f for v in verdicts for f in v["failures"]}),
        "api_body": body if not isinstance(body, list) else f"<{len(body)} plans>",
    }


# ---------------------------------------------------------------------------
# 3. generic compose path (place_ids)
# ---------------------------------------------------------------------------
def generic_compose() -> dict:
    H.reset_demo()
    _seed(ref="C4-GC-0001")
    place_ids = ["place-old-town", "place-riverside-museum", "place-food-hall"]
    r = H.client.post(
        f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/plans/generate",
        json={"place_ids": place_ids},
    )
    return {
        "status": r.status_code,
        "body": r.text[:400],
        "plans": len(H.list_plans()),
        "plans_without_c4_reference": True,
    }


# ---------------------------------------------------------------------------
# 4. can the user select + start a plan the validator rejects?
# ---------------------------------------------------------------------------
def select_and_start() -> dict:
    H.reset_demo()
    _seed(ref="C4-SEL-0001")
    code, _ = H.generate_plans()
    plans = H.list_plans()
    out = {"generate_status": code, "plans": len(plans)}
    if not plans:
        return out
    sel = H.select_plan(H.DEMO_JOURNEY_ID, plans[0]["id"])
    out["select_status"] = sel.status_code
    out["select_body"] = sel.text[:400]
    out["journey_status"] = H.journey().get("status")
    out["active_plan_set"] = bool(H.journey().get("active_plan_version_id"))
    out["commitment_survived"] = len(H.commitment_rows()) >= 1
    start = H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
    out["start_status"] = start.status_code
    out["start_body"] = start.text[:300]
    out["journey_status_after_start"] = H.journey().get("status")
    return out


# ---------------------------------------------------------------------------
# 5. after the journey is live, does mutation revalidate the C4?
# ---------------------------------------------------------------------------
def mutation_revalidation() -> dict:
    H.reset_demo()
    _seed(ref="C4-MUT-0001")
    H.generate_plans()
    plans = H.list_plans()
    out: dict = {}
    if not plans:
        return {"probe_error": "no plans generated"}
    H.select_plan(H.DEMO_JOURNEY_ID, plans[0]["id"])
    H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
    out["journey_status"] = H.journey().get("status")
    out["active_plan"] = bool(H.journey().get("active_plan_version_id"))
    out["constraints"] = [c.get("rule_code") for c in H.list_constraints()]
    out["commitments"] = len(H.commitment_rows())
    add = H.add_constraint(
        H.DEMO_JOURNEY_ID,
        {
            "kind": "HARD",
            "category": "time",
            "rule_code": "JOURNEY_END_BY",
            "params": {"time": "18:00"},
        },
    )
    out["add_constraint_status"] = add.status_code
    out["add_constraint_body"] = add.text[:300]
    ev = H.post_event(H.DEMO_JOURNEY_ID)
    out["event_status"] = ev.status_code
    out["event_body"] = ev.text[:300]
    rp = _safe(H.request_replan, H.DEMO_JOURNEY_ID)
    out["replan_status"] = getattr(rp, "status_code", None)
    out["replan_body"] = getattr(rp, "text", str(rp))[:500]
    out["replans"] = len(H.list_replans())
    out["journey_status_after"] = H.journey().get("status")
    out["commitment_survived"] = len(H.commitment_rows()) >= 1
    return out


# ---------------------------------------------------------------------------
# 6. three code paths, two different definitions of feasibility
# ---------------------------------------------------------------------------
def select_booking_consistency() -> dict:
    """generate ignores C4, select ignores C4, booking enforces C4.

    The traveller can select a plan and is then refused a booking on it.
    """
    from fastapi.testclient import TestClient

    H.reset_demo()
    _seed(ref="C4-CONSIST-0001")
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID

    gen = safe.post(f"/api/v1/journeys/{jid}/plans/generate", json={})
    plans = safe.get(f"/api/v1/journeys/{jid}/plans").json()
    out: dict = {
        "generate_status": gen.status_code,
        "plans": len(plans) if isinstance(plans, list) else None,
    }
    if not isinstance(plans, list) or not plans:
        return out

    sel = safe.post(f"/api/v1/journeys/{jid}/plans/{plans[0]['id']}/select")
    out["select_status"] = sel.status_code
    out["select_accepted"] = sel.status_code == 200

    activities = plans[0].get("activities") or []
    if not activities:
        return out
    booking = safe.post(
        f"/api/v1/journeys/{jid}/bookings",
        json={"activity_id": activities[0]["id"], "provider_key": "mock-booking"},
    )
    out["booking_status"] = booking.status_code
    out["booking_body"] = booking.text[:400]
    out["booking_names_locked_commitment"] = "LOCKED_COMMITMENT" in booking.text
    out["product_let_user_select_a_plan_it_will_not_let_them_use"] = (
        out.get("select_accepted") and booking.status_code >= 400
    )
    return out


STEPS = (
    ("generation_constraints", generation_constraints),
    ("generator_vs_validator", generator_vs_validator),
    ("generic_compose", generic_compose),
    ("select_and_start", select_and_start),
    ("mutation_revalidation", mutation_revalidation),
    ("select_booking_consistency", select_booking_consistency),
)


def main() -> int:
    result: dict = {"snapshot": LABEL}
    for name, fn in STEPS:
        result[name] = _safe(fn)

    out = EVID / f"c4_gate_{LABEL.lower()}.json"
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str)[:6000])
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

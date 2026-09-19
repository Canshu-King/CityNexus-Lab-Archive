"""Attack surface 1: is there ONE feasibility truth across the planning paths?

The V19.2 gate asks whether these four agree about the same journey:

    generate_plans()               POST /plans/generate          (initial composition)
    _generic_compose_plans()       POST /plans/generate {place_ids}
    validate_plan_feasibility()    the function select/booking call
    select / booking               POST /plans/{id}/select, POST /bookings

A product that lets a traveller *select* a plan and then refuses to *book* it is
the split-brain defect.  This probe records the exact status codes, the failure
codes each path reports, and whether any path accepts something another rejects.

Usage:
    python tools/v192_probe_feasibility_truth.py [A|B|C]
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = Path(os.environ.get("V192_EVID", LAB / "evidence"))

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _body(resp) -> dict:
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return {"__raw__": resp.text[:400]}


def _failure_codes(payload) -> list[str]:
    """Pull rule codes out of whatever shape a failure payload has."""
    found: list[str] = []
    stack = [payload]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"rule_code", "code", "failure", "reason"} and isinstance(value, str):
                    found.append(value)
                elif key in {"failures", "violations", "reasons", "details", "blockers"}:
                    stack.append(value)
                elif isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, str):
            found.append(node)
    return sorted({f for f in found if f})


def scenario(name: str, *, reservation: dict | None, place_ids=None, capabilities=None) -> dict:
    H.reset_demo()
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID
    out: dict = {"scenario": name}

    if capabilities is not None:
        out["capability_put"] = H.put_traveler_capabilities(capabilities).status_code
        out["capability_confirm"] = H.confirm_traveler_capabilities(capabilities).status_code

    if reservation is not None:
        imp = safe.post(
            f"/api/v1/journeys/{jid}/inbox/import",
            json={"artifact_type": "STRUCTURED_JSON", "payload": {"reservation": reservation}},
        )
        out["import"] = imp.status_code
        if imp.status_code in (200, 201):
            conf = safe.post(f"/api/v1/journeys/{jid}/inbox/{imp.json()['id']}/confirm")
            out["confirm"] = conf.status_code
            commitment = _body(conf).get("commitment") or {}
            out["commitment"] = {
                "level": commitment.get("level"),
                "status": commitment.get("status"),
                "semantic_key": (commitment.get("policy") or {}).get("semantic_key"),
            }
        else:
            out["import_body"] = imp.text[:300]
            return out

    # --- path 1: generate_plans() ------------------------------------------
    payload = {"place_ids": place_ids} if place_ids else {}
    status, body = H.generate_plans(jid, **payload)
    out["generate_status"] = status
    out["generate_failure_codes"] = _failure_codes(body)
    out["generate_body_head"] = json.dumps(body, ensure_ascii=False)[:300]

    plans = H.list_plans(jid)
    out["plans_after_generate"] = len(plans)

    # --- path 2: the validator that select/booking use ---------------------
    try:
        # V19.2 moved this out of app.replanning.feasibility into app.services.
        from app.services import validate_plan_feasibility

        journey_obj = H.journey(jid)
        session = H._session()
        try:
            from app.db.models import Journey as JourneyModel, PlanVersion as PlanModel

            jrow = session.get(JourneyModel, jid)
            if plans:
                verdicts = []
                for plan in plans[:3]:
                    prow = session.get(PlanModel, plan.get("id"))
                    verdict = validate_plan_feasibility(
                        session, jrow, prow, include_active_c4=True
                    )
                    verdicts.append(
                        {
                            "plan_id": plan.get("id"),
                            "feasible": getattr(verdict, "passed", verdict)
                            if not isinstance(verdict, dict)
                            else verdict.get("feasible"),
                            "failures": list(getattr(verdict, "failures", []) or [])
                            if not isinstance(verdict, dict)
                            else _failure_codes(verdict),
                        }
                    )
                out["validator"] = verdicts
                out["generator_produced_plans_the_validator_rejects"] = any(
                    v.get("feasible") is False for v in verdicts
                )
            else:
                out["validator"] = "no plans to validate"
        finally:
            session.close()
    except Exception as exc:  # noqa: BLE001
        out["validator_error"] = f"{type(exc).__name__}: {exc}"
        out["validator_traceback_tail"] = traceback.format_exc().splitlines()[-6:]

    if not plans:
        out["select"] = "skipped (no plans)"
        out["booking"] = "skipped (no plans)"
        out["journey_status"] = H.journey(jid).get("status")
        return out

    # --- path 3: select ----------------------------------------------------
    sel = safe.post(f"/api/v1/journeys/{jid}/plans/{plans[0]['id']}/select")
    out["select"] = sel.status_code
    out["select_body_head"] = json.dumps(_body(sel), ensure_ascii=False)[:250]
    out["product_let_user_select"] = sel.status_code == 200

    # --- path 4: booking (needs a real activity_id from the selected plan) --
    activity_id = None
    try:
        session = H._session()
        try:
            from app.db.models import Activity as ActivityModel

            activity_id = session.scalar(
                __import__("sqlalchemy").select(ActivityModel.id)
                .where(ActivityModel.plan_version_id == plans[0]["id"])
                .limit(1)
            )
        finally:
            session.close()
    except Exception as exc:  # noqa: BLE001
        out["activity_lookup_error"] = f"{type(exc).__name__}: {exc}"

    if activity_id is None:
        out["booking"] = "skipped (no activity id)"
        out["journey_status"] = H.journey(jid).get("status")
        return out

    book = safe.post(
        f"/api/v1/journeys/{jid}/bookings",
        json={"activity_id": str(activity_id), "provider_key": "mock-booking"},
    )
    out["booking"] = book.status_code
    out["booking_failure_codes"] = _failure_codes(_body(book))
    out["booking_body_head"] = json.dumps(_body(book), ensure_ascii=False)[:250]
    out["product_let_user_select_a_plan_it_will_not_let_them_use"] = (
        out["select"] == 200 and book.status_code >= 400
    )

    out["journey_status"] = H.journey(jid).get("status")
    out["experience"] = safe.get(f"/api/v1/journeys/{jid}/experience").status_code
    out["twin"] = safe.get(f"/api/v1/journeys/{jid}/twin").status_code
    return out


def main() -> int:
    arrival = H.c4_reservation(
        confirmation_ref="C4R-ARRIVAL",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
        anchor_role="ARRIVAL",
    )
    departure = H.c4_reservation(
        confirmation_ref="C4R-DEPARTURE",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
        anchor_role="DEPARTURE",
    )

    cases = [
        ("control: no reservation", None, None, None),
        ("ARRIVAL C4 (routable anchor missing)", arrival, None, None),
        ("DEPARTURE C4", departure, None, None),
        ("control: generic compose, no reservation", None, ["place-old-town", "place-riverside-museum"], None),
        (
            "capability: impossible HARD walking cap (1 m)",
            None,
            None,
            [H.capability("MAX_WALKING_PER_LEG_M", "HARD", params={"max_m": 1})],
        ),
        (
            "capability: reasonable HARD walking cap (800 m)",
            None,
            None,
            [H.capability("MAX_WALKING_PER_LEG_M", "HARD", params={"max_m": 800})],
        ),
    ]

    result: dict = {"snapshot": LABEL, "snapshot_dir": str(SNAP), "cases": []}
    for name, reservation, place_ids, capabilities in cases:
        try:
            result["cases"].append(
                scenario(
                    name,
                    reservation=reservation,
                    place_ids=place_ids,
                    capabilities=capabilities,
                )
            )
        except Exception as exc:  # noqa: BLE001
            result["cases"].append(
                {
                    "scenario": name,
                    "probe_error": f"{type(exc).__name__}: {exc}",
                    "traceback_tail": traceback.format_exc().splitlines()[-8:],
                }
            )

    split = [
        c["scenario"]
        for c in result["cases"]
        if c.get("product_let_user_select_a_plan_it_will_not_let_them_use")
    ]
    gen_rejected = [
        c["scenario"]
        for c in result["cases"]
        if c.get("generator_produced_plans_the_validator_rejects")
    ]
    result["summary"] = {
        "split_brain_select_ok_booking_rejected": split,
        "generator_produced_plans_the_validator_rejects": gen_rejected,
        "single_feasibility_truth": not split and not gen_rejected,
    }

    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / f"feasibility_truth_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

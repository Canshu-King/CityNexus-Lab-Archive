"""V19.1: capability <-> C4 commitment conflict surfaces (re-check of the V19 findings).

Re-tests the previous round's F7b / F7c / F7d against the CURRENT tree, and adds the
two questions the previous round did not ask:

  * can a HARD accessibility need be downgraded to STRONG through the public API?
  * does a TRAVELER-scoped need block every future journey for that traveller?

Usage:  python tools/v191_probe_commitment_conflict.py [A|B]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = LAB / "evidence"

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402

CONFLICT_WORDS = ("conflict", "step_free", "accessib", "commitment", "capabilit")
CRUISE = "place-river-cruise"


def _seed_cruise(ref: str = "V191-CRUISE-PAID") -> dict:
    """A paid cruise, anchored MID_TRIP to a real place (the V19 configuration)."""
    reservation = {
        "reservation_type": "FERRY",
        "confirmation_ref": ref,
        "origin": {"name": "Nexus Pier"},
        "destination": {"name": "Nexus River Cruise"},
        "scheduled_departure_at": "2026-10-10T15:30:00+08:00",
        "scheduled_arrival_at": "2026-10-10T16:30:00+08:00",
        "anchor_role": "MID_TRIP",
        "semantic_node_key": CRUISE,
        "provider_key": "user-confirmed-cruise",
        "price_amount_minor": 12000,
        "currency": "CNY",
    }
    imp = H.inbox_import(H.DEMO_JOURNEY_ID, reservation)
    if imp.status_code not in (200, 201):
        return {"import_status": imp.status_code, "body": imp.text[:300]}
    conf = H.inbox_confirm(H.DEMO_JOURNEY_ID, imp.json()["id"])
    return {
        "import_status": imp.status_code,
        "confirm_status": conf.status_code,
        "commitment": (conf.json().get("commitment") if conf.status_code == 200 else None),
    }


def _safe_client():
    from fastapi.testclient import TestClient

    return TestClient(H.main_module.app, raise_server_exceptions=False)


def _surfaces() -> dict:
    """Every traveller-facing surface, checked for conflict/capability vocabulary.

    Uses raise_server_exceptions=False so a 500 is recorded as evidence rather than
    aborting the probe.
    """
    safe = _safe_client()
    jid = H.DEMO_JOURNEY_ID
    out = {}
    for label, resp in (
        ("experience", safe.get(f"/api/v1/journeys/{jid}/experience")),
        ("twin", safe.get(f"/api/v1/journeys/{jid}/twin")),
        ("constraints", safe.get(f"/api/v1/journeys/{jid}/constraints")),
        ("traveler_twin", safe.get(f"/api/v1/travelers/{H.DEMO_TRAVELER_ID}/traveler-twin")),
        ("journey", safe.get(f"/api/v1/journeys/{jid}")),
    ):
        text = resp.text.lower()
        out[label] = {
            "status": resp.status_code,
            **{f"mentions_{w}": w in text for w in CONFLICT_WORDS},
        }
    return out


def _evidence(level: str | None) -> None:
    """level=None -> clear; otherwise write accessibility metadata on every place."""
    from sqlalchemy import select

    from app.db.models import Place

    with H._session() as s:
        for row in s.scalars(select(Place)).all():
            meta = json.loads(row.metadata_json or "{}")
            if level is None:
                meta.pop("accessibility", None)
            else:
                meta["accessibility"] = level
            row.metadata_json = json.dumps(meta, ensure_ascii=False)
        s.commit()


def hard_vs_c4() -> dict:
    """F7b: a HARD capability against a paid commitment."""
    H.reset_demo()
    _evidence(None)
    seed = _seed_cruise()
    code, body = H.generate_plans()
    baseline_plans = len(H.list_plans())
    cap = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    code2, body2 = H.generate_plans()
    plans = H.list_plans()
    cruise_in_plans = [
        any(a.get("place_id") == CRUISE for a in p.get("activities", [])) for p in plans
    ]
    return {
        "c4_confirm_status": seed.get("confirm_status"),
        "c4_level": (seed.get("commitment") or {}).get("level"),
        "baseline_generate": code,
        "baseline_plans": baseline_plans,
        "capability_status": cap.status_code,
        "conflict_generate": code2,
        "conflict_plans": len(plans),
        "cruise_present": cruise_in_plans,
        "error_message": (
            (body2 or {}).get("error", {}).get("message") if isinstance(body2, dict) else None
        ),
        "commitments_after": H.commitment_rows(),
        "commitment_survived": len(H.commitment_rows()) >= 1,
        "surfaces": _surfaces(),
    }


def soft_vs_c4() -> dict:
    """F7c: a SOFT capability against a paid commitment that is known-inaccessible."""
    H.reset_demo()
    _evidence({"stairs": True, "step_free": False})  # the cruise pier has stairs
    seed = _seed_cruise("V191-CRUISE-SOFT")
    cap = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "SOFT")])
    code, body = H.generate_plans()
    plans = H.list_plans()
    cruise_in_plans = [
        any(a.get("place_id") == CRUISE for a in p.get("activities", [])) for p in plans
    ]
    blob = json.dumps(body if isinstance(body, dict) else plans, ensure_ascii=False).lower()
    _evidence(None)
    return {
        "c4_confirm_status": seed.get("confirm_status"),
        "capability_status": cap.status_code,
        "persisted_severity": [
            c.get("severity") for c in H.capability_rows("JOURNEY")
        ],
        "generate": code,
        "plans": len(plans),
        "cruise_present": cruise_in_plans,
        "plan_silently_includes_obstructed_anchor": any(cruise_in_plans),
        "any_warning_in_body": any(w in blob for w in ("conflict", "warning", "step_free", "accessib")),
        "surfaces": _surfaces(),
    }


def robust_flag() -> dict:
    """F7d: does the journey still report itself robust while no plan exists?"""
    H.reset_demo()
    _evidence(None)
    H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    code, _ = H.generate_plans()
    plans = H.list_plans()
    twin = H.journey_twin()
    experience_status = None
    try:
        H.experience()
        experience_status = 200
    except Exception:  # noqa: BLE001
        from fastapi.testclient import TestClient

        safe = TestClient(H.main_module.app, raise_server_exceptions=False)
        experience_status = safe.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/experience").status_code
    envelope = twin.get("feasibility_envelope") or {}
    return {
        "generate": code,
        "plans": len(plans),
        "plan_exists": bool(plans),
        "twin_robust": envelope.get("robust"),
        "twin_risk_reason_codes": envelope.get("risk_reason_codes"),
        "twin_keys": sorted(twin),
        "experience_status": experience_status,
        "robust_true_while_no_plan": envelope.get("robust") is True and not plans,
    }


def hard_downgrade() -> dict:
    """Can the public API demote a HARD accessibility need to STRONG?"""
    H.reset_demo()
    _evidence(None)
    first = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    before = H.capability_rows("JOURNEY")
    downgrade = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "STRONG")])
    after = H.capability_rows("JOURNEY")
    code, _ = H.generate_plans()
    return {
        "declare_hard_status": first.status_code,
        "before": before,
        "downgrade_status": downgrade.status_code,
        "after": after,
        "severity_downgraded": bool(before and after and before[0].get("severity") == "HARD"
                                    and after[0].get("severity") != "HARD"),
        "class_still_says_hard": bool(after and after[0].get("class") == "HARD_ACCESSIBILITY_NEED"),
        "generate_after_downgrade": code,
        "plans_after_downgrade": len(H.list_plans()),
        "audit": [a["action"] for a in H.audit_rows("capability")],
    }


def traveler_scope_blocks_future_journeys() -> dict:
    """A TRAVELER-scoped need must not make every future journey unplannable."""
    H.reset_demo()
    _evidence(None)
    trav = H.confirm_traveler_capabilities([H.capability("AVOID_STAIRS", "HARD")])
    second = H.client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": H.DEMO_TRAVELER_ID,
            "title": "second journey",
            "city_code": "CNX-DEMO",
            "timezone": "Asia/Shanghai",
            "start_at": "2026-11-01T09:00:00+08:00",
            "end_at": "2026-11-01T19:00:00+08:00",
            "budget": {"amount_minor": 200000, "currency": "CNY"},
        },
    )
    out = {
        "traveler_capability_status": trav.status_code,
        "create_second_status": second.status_code,
    }
    if second.status_code in (200, 201):
        jid = second.json()["id"]
        code, body = H.generate_plans(jid)
        out["second_generate"] = code
        out["second_plans"] = len(H.list_plans(jid))
        out["second_constraints"] = [
            c.get("rule_code") for c in H.list_constraints(jid)
        ]
        out["second_capabilities"] = H.get_journey_capabilities(jid).get("capabilities")
        out["error_message"] = (
            (body or {}).get("error", {}).get("message") if isinstance(body, dict) else None
        )
        out["future_journey_blocked"] = code != 201
    return out


def main() -> int:
    result: dict = {"snapshot": LABEL}
    for name, fn in (
        ("hard_vs_c4", hard_vs_c4),
        ("soft_vs_c4", soft_vs_c4),
        ("robust_flag", robust_flag),
        ("hard_downgrade", hard_downgrade),
        ("traveler_scope_blocks_future_journeys", traveler_scope_blocks_future_journeys),
    ):
        try:
            result[name] = fn()
        except Exception as exc:  # noqa: BLE001
            result[name] = {"probe_error": f"{type(exc).__name__}: {exc}"}

    out = EVID / f"commitment_conflict_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str)[:7000])
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

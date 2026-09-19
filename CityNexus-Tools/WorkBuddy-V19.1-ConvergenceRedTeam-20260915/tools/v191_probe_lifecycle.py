"""V19.1 probe: feasibility/evidence, mid-trip lifecycle, C4 conflict, scope, audit, Hermes.

Drives the FastAPI app in-process against the snapshot's own throwaway SQLite DB.
Never touches the main worktree.

Usage:
    python tools/v191_probe_lifecycle.py [A|B]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = LAB / "evidence"

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402


# ---------------------------------------------------------------------------
# place evidence injection (test-only; writes to the snapshot DB)
# ---------------------------------------------------------------------------
def _place_ids() -> list[str]:
    from sqlalchemy import select

    from app.db.models import Place

    with H._session() as s:
        return [p.id for p in s.scalars(select(Place)).all()]


def set_place_evidence(accessibility: dict | None) -> dict:
    """Write accessibility evidence onto every place in the snapshot DB."""
    from sqlalchemy import select

    from app.db.models import Place

    with H._session() as s:
        rows = list(s.scalars(select(Place)).all())
        for row in rows:
            meta = json.loads(row.metadata_json or "{}")
            if accessibility is None:
                meta.pop("accessibility", None)
            else:
                meta["accessibility"] = accessibility
            row.metadata_json = json.dumps(meta, ensure_ascii=False)
        s.commit()
        return {"places": len(rows), "accessibility": accessibility}


def clear_capabilities() -> None:
    from sqlalchemy import delete

    from app.db.models import TravelerCapability

    with H._session() as s:
        s.execute(delete(TravelerCapability))
        s.commit()


# ---------------------------------------------------------------------------
# 1. evidence matrix through the real HTTP surface
# ---------------------------------------------------------------------------
def evidence_matrix() -> dict:
    out: dict = {}
    scenarios = {
        "no_capability": None,
        "capability_evidence_missing": None,
        "capability_evidence_verified": {"step_free": True, "wheelchair_access": True},
        "capability_evidence_unknown": {"evidence_status": "UNKNOWN"},
        "capability_evidence_conflict": {"stairs": True, "step_free": False},
        "capability_evidence_verified_string": {"evidence_status": "VERIFIED"},
    }
    for label, evidence in scenarios.items():
        H.reset_demo()
        clear_capabilities()
        if label != "no_capability":
            set_place_evidence(evidence)
        else:
            set_place_evidence(None)
        if label != "no_capability":
            r = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
            cap_status = r.status_code
        else:
            cap_status = None
        code, body = H.generate_plans()
        failures: list[str] = []
        if isinstance(body, dict):
            failures = body.get("failures") or body.get("detail") or []
            if isinstance(failures, str):
                failures = [failures]
        out[label] = {
            "capability_http_status": cap_status,
            "generate_status": code,
            "plans": len(H.list_plans()),
            "failures": failures if isinstance(failures, list) else str(failures)[:200],
            "body_keys": sorted(body) if isinstance(body, dict) else None,
        }
    set_place_evidence(None)
    clear_capabilities()
    return out


# ---------------------------------------------------------------------------
# 2. capability reaches the gate at all (projection proof)
# ---------------------------------------------------------------------------
def projection() -> dict:
    H.reset_demo()
    clear_capabilities()
    before = len(H.list_constraints())
    H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    after_rows = H.list_constraints()
    db_rows = H.constraint_rows()
    return {
        "journey_constraints_before": before,
        "journey_constraints_after": len(after_rows),
        "capability_in_constraint_api": [
            r for r in after_rows if r.get("rule_code") in H.GATE_CAPABILITY_CODES
        ],
        "capability_in_constraint_table": [
            r for r in db_rows if r.get("rule_code") in H.GATE_CAPABILITY_CODES
        ],
        "capability_rows": H.capability_rows(),
    }


# ---------------------------------------------------------------------------
# 3. mid-trip lifecycle
# ---------------------------------------------------------------------------
def midtrip() -> dict:
    H.reset_demo()
    clear_capabilities()
    set_place_evidence({"step_free": True, "wheelchair_access": True})
    code, body = H.generate_plans()
    plans = H.list_plans()
    out: dict = {
        "initial_generate_status": code,
        "initial_plans": len(plans),
    }
    if plans:
        plan_id = plans[0]["id"]
        sel = H.select_plan(H.DEMO_JOURNEY_ID, plan_id)
        out["select_status"] = sel.status_code
    start = H.client.post(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/start")
    out["start_status"] = start.status_code
    out["journey_status_after_start"] = H.journey().get("status")
    out["plan_signatures_before"] = H.plan_signatures()

    # traveller gets hurt mid-trip and needs step-free
    r_put = H.put_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    out["midtrip_put_status"] = r_put.status_code
    out["midtrip_put_body"] = _short(r_put)
    r_conf = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    out["midtrip_confirm_status"] = r_conf.status_code
    out["midtrip_confirm_body"] = _short(r_conf)
    out["journey_status_after_capability"] = H.journey().get("status")
    out["plan_signatures_after"] = H.plan_signatures()
    out["plans_mutated_silently"] = out["plan_signatures_before"] != out["plan_signatures_after"]
    out["replan_proposals"] = len(H.list_replans())
    out["audit_capability"] = [a["action"] for a in H.audit_rows("capability")]

    # recovery / review semantics
    try:
        exp = H.experience()
        out["experience_status"] = 200
        out["experience_keys"] = sorted(exp)
        blob = json.dumps(exp, ensure_ascii=False)
        out["experience_mentions_capability"] = "capabilit" in blob.lower()
        out["experience_mentions_review"] = "review" in blob.lower()
    except Exception as exc:  # noqa: BLE001
        from fastapi.testclient import TestClient

        probe = TestClient(H.main_module.app, raise_server_exceptions=False)
        r = probe.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/experience")
        out["experience_status"] = r.status_code
        out["experience_error"] = f"{type(exc).__name__}: {exc}"
    set_place_evidence(None)
    clear_capabilities()
    return out


# ---------------------------------------------------------------------------
# 4. capability vs C4 commitment
# ---------------------------------------------------------------------------
def _failures(body) -> list[str]:
    if not isinstance(body, dict):
        return []
    raw = body.get("failures") or body.get("detail") or []
    return raw if isinstance(raw, list) else [raw]


def _mentions(blob: str, *needles: str) -> bool:
    low = blob.upper()
    return any(n.upper() in low for n in needles)


def conflict() -> dict:
    """Build a genuine C4_Anchored commitment, then collide it with hard capability needs.

    The commitment is created through the production HTTP path
    (inbox/import -> inbox/{draft}/confirm), so the gate sees exactly what a real
    user-confirmed external reservation produces.
    """
    out: dict = {}

    # -- A: the C4 must be visible to the constraint surface at all ----------
    H.reset_demo()
    clear_capabilities()
    set_place_evidence(None)
    seed = H.seed_c4_commitment()
    out["c4_seed"] = {
        "import_status": seed.get("import_status"),
        "confirm_status": seed.get("confirm_status"),
        "draft_status": seed.get("draft_status"),
        "commitment_level": (seed.get("commitment") or {}).get("level"),
        "commitment_status": (seed.get("commitment") or {}).get("status"),
        "semantic_key": ((seed.get("commitment") or {}).get("policy") or {}).get("semantic_key"),
        "scheduled_start_at": ((seed.get("commitment") or {}).get("policy") or {}).get(
            "scheduled_start_at"
        ),
    }
    constraint_codes = [c.get("rule_code") for c in H.list_constraints()]
    out["c4_projected_into_constraints"] = "LOCKED_COMMITMENT" in constraint_codes
    out["constraint_codes_after_c4"] = sorted({c for c in constraint_codes if c})

    # -- B: C4 + unsatisfiable hard accessibility ---------------------------
    # Every place is a stairs-only venue, so STEP_FREE_REQUIRED cannot be met.
    set_place_evidence({"stairs": True, "step_free": False})
    cap = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    out["hard_capability_status"] = cap.status_code
    code, body = H.generate_plans()
    out["accessibility_conflict"] = {
        "generate_status": code,
        "plans": len(H.list_plans()),
        "body_keys": sorted(body) if isinstance(body, dict) else None,
        "message": (body or {}).get("error", {}).get("message") if isinstance(body, dict) else None,
        "failures": _failures(body),
        "names_capability": _mentions(json.dumps(body, default=str), "STEP_FREE", "ACCESSIBILITY"),
        "names_commitment": _mentions(json.dumps(body, default=str), "COMMITMENT"),
        "commitments_after": len(H.commitment_rows()),
        "commitment_survived": len(H.commitment_rows()) >= 1,
    }

    # -- C: does any other surface name the conflict? -----------------------
    surfaces: dict = {}
    for label, resp in (
        ("constraints", H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/constraints")),
        ("journey_twin", H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/twin")),
        ("traveler_twin", H.client.get(f"/api/v1/travelers/{H.DEMO_TRAVELER_ID}/traveler-twin")),
        ("explain", H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/plans/explain")),
        ("infeasibility", H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/infeasibility")),
        ("diagnostics", H.client.get(f"/api/v1/journeys/{H.DEMO_JOURNEY_ID}/diagnostics")),
    ):
        text = resp.text[:2000]
        surfaces[label] = {
            "status": resp.status_code,
            "mentions_step_free": _mentions(text, "STEP_FREE"),
            "mentions_accessibility": _mentions(text, "ACCESSIBILITY"),
            "mentions_commitment": _mentions(text, "COMMITMENT", "LOCKED_COMMITMENT"),
        }
    out["conflict_surfaces"] = surfaces

    cop = H.copilot(H.DEMO_JOURNEY_ID, "我用轮椅，必须全程无障碍，但现在排不出计划，为什么？")
    out["copilot_status"] = cop.status_code
    out["copilot_mentions_capability"] = _mentions(cop.text, "STEP_FREE", "无障碍", "ACCESSIBILITY")
    out["copilot_mentions_commitment"] = _mentions(cop.text, "COMMITMENT", "承诺")
    out["copilot_body"] = _short(cop)

    # -- D: C4 + rest window (capability that the C4 makes impossible) ------
    H.reset_demo()
    clear_capabilities()
    set_place_evidence({"step_free": True, "wheelchair_access": True})
    seed2 = H.seed_c4_commitment(
        confirmation_ref="C4-RAIL-0002",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
    )
    out["c4_seed_rest"] = {"confirm_status": seed2.get("confirm_status")}
    H.confirm_journey_capabilities(
        [H.capability("MIDDAY_REST_WINDOW", "HARD", params={"start": "12:00", "end": "14:00"})]
    )
    code2, body2 = H.generate_plans()
    out["rest_window_vs_c4"] = {
        "generate_status": code2,
        "plans": len(H.list_plans()),
        "failures": _failures(body2),
        "message": (body2 or {}).get("error", {}).get("message") if isinstance(body2, dict) else None,
        "names_capability": _mentions(json.dumps(body2, default=str), "REST", "MIDDAY"),
        "names_commitment": _mentions(json.dumps(body2, default=str), "COMMITMENT"),
        "commitment_survived": len(H.commitment_rows()) >= 1,
    }

    # -- E: two C4s that cannot both be honoured ---------------------------
    H.reset_demo()
    clear_capabilities()
    set_place_evidence(None)
    s3 = H.seed_c4_commitment(
        confirmation_ref="C4-RAIL-0003",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
    )
    s4 = H.seed_c4_commitment(
        confirmation_ref="C4-RAIL-0004",
        departure_at="2026-10-10T09:00:00+08:00",
        arrival_at="2026-10-10T13:00:00+08:00",
    )
    out["double_c4"] = {
        "first_confirm": s3.get("confirm_status"),
        "second_confirm": s4.get("confirm_status"),
        "commitments": len(H.commitment_rows()),
    }
    code3, body3 = H.generate_plans()
    out["double_c4"]["generate_status"] = code3
    out["double_c4"]["plans"] = len(H.list_plans())
    out["double_c4"]["commitments_after_generate"] = len(H.commitment_rows())
    out["double_c4"]["failures"] = _failures(body3)

    # -- F: same confirmation_ref twice (duplicate guard) -------------------
    H.reset_demo()
    clear_capabilities()
    d1 = H.seed_c4_commitment(confirmation_ref="C4-DUP-0001")
    d2 = H.seed_c4_commitment(confirmation_ref="C4-DUP-0001")
    out["duplicate_ref"] = {
        "first_confirm": d1.get("confirm_status"),
        "second_import": d2.get("import_status"),
        "second_confirm": d2.get("confirm_status"),
        "second_confirm_body": d2.get("confirm_body"),
        "commitments": len(H.commitment_rows()),
        "duplicate_rejected": d2.get("confirm_status") == 409,
    }

    # -- G: does the C4 actually constrain generation? ----------------------
    # Identical journey, with and without the C4 arrival anchor.
    H.reset_demo()
    clear_capabilities()
    set_place_evidence(None)
    code_free, _ = H.generate_plans()
    baseline_sigs = H.plan_signatures()
    baseline_titles = sorted(
        a.get("title") for p in H.list_plans() for a in p.get("activities", [])
    )
    H.reset_demo()
    clear_capabilities()
    set_place_evidence(None)
    seed_c4 = H.seed_c4_commitment(
        confirmation_ref="C4-ANCHOR-0001",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
    )
    code_c4, body_c4 = H.generate_plans()
    c4_sigs = H.plan_signatures()
    c4_titles = sorted(
        a.get("title") for p in H.list_plans() for a in p.get("activities", [])
    )
    out["c4_influence"] = {
        "c4_confirm_status": seed_c4.get("confirm_status"),
        "baseline_generate_status": code_free,
        "baseline_plans": len(baseline_sigs),
        "with_c4_generate_status": code_c4,
        "with_c4_plans": len(c4_sigs),
        "plans_differ": baseline_sigs != c4_sigs,
        "baseline_titles": baseline_titles,
        "with_c4_titles": c4_titles,
        "failures": _failures(body_c4),
    }

    set_place_evidence(None)
    clear_capabilities()
    return out


# ---------------------------------------------------------------------------
# 5. scope isolation + audit
# ---------------------------------------------------------------------------
def scope_audit() -> dict:
    H.reset_demo()
    clear_capabilities()
    out: dict = {}
    # journey-scoped hard need
    r1 = H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "HARD")])
    out["journey_capability_status"] = r1.status_code
    out["rows_after_journey"] = H.capability_rows()
    # traveller-scoped
    r2 = H.confirm_traveler_capabilities([H.capability("AVOID_STAIRS", "HARD")])
    out["traveler_capability_status"] = r2.status_code
    out["rows_after_traveler"] = H.capability_rows()
    out["traveler_endpoint_scope_forced"] = all(
        c["scope"] == "TRAVELER" for c in H.capability_rows("TRAVELER")
    )
    out["journey_endpoint_scope_forced"] = all(
        c["scope"] == "JOURNEY" for c in H.capability_rows("JOURNEY")
    )
    # a second journey must not inherit the journey-scoped need
    r3 = H.client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": H.DEMO_TRAVELER_ID,
            "title": "second journey",
            "city_code": "TJN",
            "timezone": "Asia/Shanghai",
            "start_at": "2026-11-01T09:00:00+08:00",
            "end_at": "2026-11-01T19:00:00+08:00",
            "budget": {"amount_minor": 200000, "currency": "CNY"},
        },
    )
    out["create_journey_status"] = r3.status_code
    if r3.status_code in (200, 201):
        jid = r3.json().get("id")
        out["second_journey_id"] = jid
        out["second_journey_constraints"] = [
            c for c in H.list_constraints(jid) if c.get("rule_code") in H.GATE_CAPABILITY_CODES
        ]
        out["second_journey_capabilities"] = H.get_journey_capabilities(jid).get("capabilities")
        code, body = H.generate_plans(jid)
        out["second_journey_generate_status"] = code
        out["second_journey_plans"] = len(H.list_plans(jid))
    else:
        out["create_journey_body"] = _short(r3)
    # update + deactivate
    H.confirm_journey_capabilities([H.capability("STEP_FREE_REQUIRED", "STRONG")])
    out["rows_after_downgrade_attempt"] = H.capability_rows("JOURNEY")
    H.confirm_journey_capabilities([])
    out["rows_after_deactivate"] = H.capability_rows("JOURNEY")
    out["audit_actions"] = sorted({a["action"] for a in H.audit_rows() if "capability" in (a["action"] or "")})
    out["audit_rows"] = H.audit_rows("capability")
    clear_capabilities()
    return out


# ---------------------------------------------------------------------------
# 6. Hermes capability context
# ---------------------------------------------------------------------------
def _tool_names(tools) -> list[str]:
    names = []
    for t in tools or []:
        if isinstance(t, dict):
            names.append(str(t.get("name") or t.get("tool") or t.get("id") or "")[:48])
        else:
            names.append(str(t)[:48])
    return sorted(set(n for n in names if n))


def hermes() -> dict:
    H.reset_demo()
    clear_capabilities()
    tools = H.agent_tools()
    tools_v2 = H.agent_tools("v2")
    names = _tool_names(tools)
    names_v2 = _tool_names(tools_v2)
    blob = json.dumps(tools, ensure_ascii=False, default=str).lower()
    out = {
        "tool_count_v1": len(tools),
        "tool_count_v2": len(tools_v2),
        "tool_names_v1": names,
        "tool_names_v2": names_v2,
        "any_capability_tool": "capabilit" in blob,
        "hermes_capabilities_endpoint": H.client.get("/api/v1/agent/hermes/capabilities").status_code,
    }
    # does any inspect tool expose capability context?
    for tool in ("inspect_journey", "inspect_twin", "get_journey", "journey_context"):
        r = H.agent_tool(tool, {"journey_id": H.DEMO_JOURNEY_ID})
        out[f"call_{tool}"] = {
            "status": r.status_code,
            "mentions_capability": "capabilit" in r.text.lower(),
        }
    # can an agent tool create/mutate a capability?
    for tool in ("create_capability", "set_capability", "update_capability"):
        probe = H.agent_tool_v2(tool, {"code": "STEP_FREE_REQUIRED", "severity": "HARD"})
        out[f"agent_{tool}_status"] = probe.status_code
    out["agent_can_create_capability"] = any(
        out.get(f"agent_{t}_status") not in (404, 405)
        for t in ("create_capability", "set_capability", "update_capability")
    )
    return out


def _short(response) -> dict:
    try:
        body = response.json()
    except ValueError:
        return {"text": response.text[:200]}
    text = json.dumps(body, ensure_ascii=False)
    return json.loads(text) if len(text) < 900 else {"preview": text[:900]}


def main() -> int:
    result = {"snapshot": LABEL}
    for name, fn in (
        ("evidence_matrix", evidence_matrix),
        ("projection", projection),
        ("midtrip", midtrip),
        ("conflict", conflict),
        ("scope_audit", scope_audit),
        ("hermes", hermes),
    ):
        try:
            result[name] = fn()
        except Exception as exc:  # noqa: BLE001
            result[name] = {"probe_error": f"{type(exc).__name__}: {exc}"}

    out = EVID / f"lifecycle_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({
        "snapshot": LABEL,
        "evidence_matrix": {
            k: {"generate_status": v.get("generate_status"), "plans": v.get("plans"),
                "failures": v.get("failures")}
            for k, v in (result.get("evidence_matrix") or {}).items()
        },
        "projection": {k: v for k, v in (result.get("projection") or {}).items()
                       if k in ("journey_constraints_before", "journey_constraints_after",
                                "capability_in_constraint_api", "capability_in_constraint_table")},
        "midtrip": result.get("midtrip"),
        "conflict": result.get("conflict"),
        "scope_audit": {k: v for k, v in (result.get("scope_audit") or {}).items()
                        if k not in ("audit_rows",)},
        "hermes": result.get("hermes"),
        "written": str(out),
    }, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

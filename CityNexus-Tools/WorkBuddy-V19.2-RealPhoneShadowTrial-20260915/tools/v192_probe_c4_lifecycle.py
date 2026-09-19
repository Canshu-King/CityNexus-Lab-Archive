"""Attack surfaces 2, 3 and the reason-propagation question.

  #2 ARRIVAL C4 start matrix  - can a journey with a confirmed C4 anchor start?
  #3 C4 confirmation idempotency - does one logical confirmation create one
     commitment, or several?
  reason propagation - when a C4 blocks planning, does the client learn WHY?

The technique that makes the reason visible: generate the plans *before* the
commitment exists, then re-validate those exact plans with
``include_active_c4=True``.  That yields the concrete failure codes instead of
the collapsed "No feasible plan candidates satisfy the journey constraints".

Usage:
    python tools/v192_probe_c4_lifecycle.py [A|B|C]
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


def _safe_body(resp) -> dict:
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return {"__raw__": resp.text[:300]}


def _validator():
    """V19.2 moved validate_plan_feasibility into app.services."""
    from app.services import validate_plan_feasibility

    return validate_plan_feasibility


def validate_plans(jid: str, plans: list[dict], *, include_c4: bool) -> list[dict]:
    fn = _validator()
    out = []
    session = H._session()
    try:
        from app.db.models import Journey as JourneyModel, PlanVersion as PlanModel

        jrow = session.get(JourneyModel, jid)
        for plan in plans[:3]:
            prow = session.get(PlanModel, plan["id"])
            verdict = fn(session, jrow, prow, include_active_c4=include_c4)
            out.append(
                {
                    "plan_id": plan["id"],
                    "passed": getattr(verdict, "passed", None),
                    "failures": list(getattr(verdict, "failures", []) or []),
                }
            )
    finally:
        session.close()
    return out


def anchor_case(anchor_role: str, arrival_at: str, semantic_node_key: str | None) -> dict:
    """Generate first, then attach the anchor, so the reason stays visible."""
    H.reset_demo()
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID
    out: dict = {
        "anchor_role": anchor_role,
        "scheduled_arrival_at": arrival_at,
        "semantic_node_key": semantic_node_key,
    }

    # 1. plans exist and are feasible BEFORE the anchor exists
    status, body = H.generate_plans(jid)
    plans = H.list_plans(jid)
    out["generate_before_anchor"] = status
    out["plans_before_anchor"] = len(plans)
    if not plans:
        out["abort"] = "no plans without an anchor"
        return out
    out["validator_before_anchor"] = validate_plans(jid, plans, include_c4=False)

    # 2. attach the anchor
    reservation = H.c4_reservation(
        confirmation_ref=f"C4R-{anchor_role}-{arrival_at}",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at=arrival_at,
        anchor_role=anchor_role,
    )
    if semantic_node_key:
        reservation["semantic_node_key"] = semantic_node_key
    imp = safe.post(
        f"/api/v1/journeys/{jid}/inbox/import",
        json={"artifact_type": "STRUCTURED_JSON", "payload": {"reservation": reservation}},
    )
    out["import"] = imp.status_code
    if imp.status_code not in (200, 201):
        out["import_body"] = imp.text[:300]
        return out
    conf = safe.post(f"/api/v1/journeys/{jid}/inbox/{imp.json()['id']}/confirm")
    out["confirm"] = conf.status_code
    commitment = _safe_body(conf).get("commitment") or {}
    out["commitment_level"] = commitment.get("level")
    out["commitment_status"] = commitment.get("status")
    out["commitments_after_confirm"] = len(H.commitment_rows(jid))

    # 3. re-validate the SAME plans with the anchor active -> the real reason
    out["validator_after_anchor"] = validate_plans(jid, plans, include_c4=True)
    out["anchor_blocks_existing_plans"] = any(
        v["passed"] is False for v in out["validator_after_anchor"]
    )

    # 4. select the first plan and try to start
    sel = safe.post(f"/api/v1/journeys/{jid}/plans/{plans[0]['id']}/select")
    out["select"] = sel.status_code
    if sel.status_code == 200:
        st = safe.post(f"/api/v1/journeys/{jid}/start")
        out["start"] = st.status_code
        out["start_body"] = st.text[:220]
        st2 = safe.post(f"/api/v1/journeys/{jid}/start")
        out["start_second_call"] = st2.status_code
        out["journey_status"] = H.journey(jid).get("status")
    else:
        out["select_body"] = sel.text[:220]
    out["generate_after_anchor"] = H.generate_plans(jid)[0]
    return out


def idempotency_case() -> dict:
    """The same logical confirmation must yield exactly one active commitment."""
    H.reset_demo()
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID
    out: dict = {}

    reservation = H.c4_reservation(
        confirmation_ref="C4R-IDEMPOTENT",
        departure_at="2026-10-10T08:00:00+08:00",
        arrival_at="2026-10-10T12:30:00+08:00",
        anchor_role="DEPARTURE",
    )
    payload = {"artifact_type": "STRUCTURED_JSON", "payload": {"reservation": reservation}}

    first = safe.post(f"/api/v1/journeys/{jid}/inbox/import", json=payload)
    out["import_1"] = first.status_code
    second = safe.post(f"/api/v1/journeys/{jid}/inbox/import", json=payload)
    out["import_2_same_ref"] = second.status_code
    out["import_2_body_head"] = second.text[:200]
    out["drafts_after_two_imports"] = len(_drafts(jid))

    if first.status_code not in (200, 201):
        return out
    draft_id = first.json()["id"]
    c1 = safe.post(f"/api/v1/journeys/{jid}/inbox/{draft_id}/confirm")
    out["confirm_1"] = c1.status_code
    out["commitments_after_confirm_1"] = len(H.commitment_rows(jid))
    c2 = safe.post(f"/api/v1/journeys/{jid}/inbox/{draft_id}/confirm")
    out["confirm_2_same_draft"] = c2.status_code
    out["confirm_2_body_head"] = c2.text[:200]
    out["commitments_after_confirm_2"] = len(H.commitment_rows(jid))

    # If the second import produced its own draft, confirming it must still not
    # create a second commitment for the same confirmation_ref.
    if second.status_code in (200, 201) and second.json().get("id") != draft_id:
        c3 = safe.post(f"/api/v1/journeys/{jid}/inbox/{second.json()['id']}/confirm")
        out["confirm_other_draft"] = c3.status_code
        out["commitments_after_confirm_3"] = len(H.commitment_rows(jid))

    rows = H.commitment_rows(jid)
    out["commitment_refs"] = [r.get("confirmation_ref") or r.get("external_ref") for r in rows]
    out["one_confirmation_one_commitment"] = len(rows) == 1
    return out


def _drafts(jid: str) -> list[dict]:
    r = H.client.get(f"/api/v1/journeys/{jid}/inbox")
    if r.status_code != 200:
        return []
    body = r.json()
    return body if isinstance(body, list) else body.get("items", [])


def main() -> int:
    result: dict = {"snapshot": LABEL, "snapshot_dir": str(SNAP)}

    matrix = []
    for role, arrival, node in [
        ("ARRIVAL", "2026-10-10T12:30:00+08:00", None),
        ("DEPARTURE", "2026-10-10T12:30:00+08:00", None),
        ("MID_TRIP", "2026-10-10T12:30:00+08:00", "place-old-town"),
        ("ARRIVAL", "2026-10-10T07:00:00+08:00", None),
    ]:
        try:
            matrix.append(anchor_case(role, arrival, node))
        except Exception as exc:  # noqa: BLE001
            matrix.append(
                {
                    "anchor_role": role,
                    "probe_error": f"{type(exc).__name__}: {exc}",
                    "traceback_tail": traceback.format_exc().splitlines()[-8:],
                }
            )
    result["anchor_matrix"] = matrix

    try:
        result["idempotency"] = idempotency_case()
    except Exception as exc:  # noqa: BLE001
        result["idempotency"] = {
            "probe_error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc().splitlines()[-8:],
        }

    result["summary"] = {
        "anchors_blocking_existing_plans": [
            f"{c.get('anchor_role')}@{c.get('scheduled_arrival_at')}"
            for c in matrix
            if c.get("anchor_blocks_existing_plans")
        ],
        "start_statuses": {
            f"{c.get('anchor_role')}@{c.get('scheduled_arrival_at')}": c.get("start")
            for c in matrix
            if c.get("start") is not None
        },
        "any_start_5xx": any(
            isinstance(c.get("start"), int) and c["start"] >= 500 for c in matrix
        ),
        "one_confirmation_one_commitment": result.get("idempotency", {}).get(
            "one_confirmation_one_commitment"
        ),
    }

    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / f"c4_lifecycle_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

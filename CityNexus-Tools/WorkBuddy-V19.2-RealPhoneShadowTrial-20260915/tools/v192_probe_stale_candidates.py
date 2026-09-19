"""Attack surface 9: stale candidate lifecycle.

A plan whose frozen mobility evidence has expired or been invalidated must stop
being offered as a viable choice.  The failure mode to look for is a stale
candidate that the UI still lists as selectable, or an ACTIVE journey that keeps
running on expired evidence without telling anyone.

Technique: generate plans, then mutate the frozen evidence of a *candidate* and
of the *selected* plan directly in the throwaway snapshot database.  Only the
lab's own DB is touched.

Usage:
    python tools/v192_probe_stale_candidates.py [A|C]
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = Path(os.environ.get("V192_EVID", LAB / "evidence"))

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _plans_via_api(jid: str) -> list[dict]:
    return H.list_plans(jid)


def _mutate_evidence(plan_id: str, *, mode: str) -> dict:
    """Rewrite a plan's frozen evidence in the lab database only."""
    session = H._session()
    try:
        from app.db.models import PlanVersion as PlanModel

        row = session.get(PlanModel, plan_id)
        if row is None:
            return {"error": "plan not found"}
        raw = json.loads(row.mobility_evidence_json or "{}")
        before = {
            "snapshot_id": raw.get("snapshot_id"),
            "expires_at": raw.get("expires_at"),
            "column_snapshot_id": row.mobility_snapshot_id,
        }
        if mode == "expired":
            raw["expires_at"] = (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat()
        elif mode == "missing_snapshot_id":
            raw.pop("snapshot_id", None)
        elif mode == "inconsistent_reference":
            raw["snapshot_id"] = "00000000-0000-4000-8000-000000000000"
        elif mode == "invalid_timestamp":
            raw["expires_at"] = "not-a-timestamp"
        row.mobility_evidence_json = json.dumps(raw)
        session.commit()
        return {"before": before, "after_mode": mode}
    finally:
        session.close()


def _restore_evidence(plan_id: str, original: str) -> None:
    session = H._session()
    try:
        from app.db.models import PlanVersion as PlanModel

        row = session.get(PlanModel, plan_id)
        if row is not None:
            row.mobility_evidence_json = original
            session.commit()
    finally:
        session.close()


def _original(plan_id: str) -> str:
    session = H._session()
    try:
        from app.db.models import PlanVersion as PlanModel

        row = session.get(PlanModel, plan_id)
        return row.mobility_evidence_json if row is not None else ""
    finally:
        session.close()


def main() -> int:
    H.reset_demo()
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID
    result: dict = {"snapshot": LABEL, "snapshot_dir": str(SNAP)}

    status, _ = H.generate_plans(jid)
    plans = _plans_via_api(jid)
    result["generate"] = status
    result["plans"] = len(plans)
    if len(plans) < 3:
        result["abort"] = "need at least 3 plans"
        EVID.mkdir(parents=True, exist_ok=True)
        (EVID / f"stale_candidates_{LABEL.lower()}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0

    candidate_id = plans[1]["id"]
    selected_id = plans[0]["id"]

    # ---- 1. stale CANDIDATE must not be selectable ------------------------
    original = _original(candidate_id)
    result["candidate_mutation"] = _mutate_evidence(candidate_id, mode="expired")
    listed = _plans_via_api(jid)
    result["candidate_still_listed"] = any(p["id"] == candidate_id for p in listed)
    result["candidate_listed_status"] = next(
        (p.get("status") for p in listed if p["id"] == candidate_id), None
    )
    sel = safe.post(f"/api/v1/journeys/{jid}/plans/{candidate_id}/select")
    result["select_stale_candidate"] = sel.status_code
    result["select_stale_body"] = sel.text[:200]
    result["stale_candidate_refused"] = sel.status_code in (409, 422)
    _restore_evidence(candidate_id, original)

    # ---- 2. every staleness shape must be refused the same way -----------
    shapes = {}
    for mode in ("expired", "missing_snapshot_id", "inconsistent_reference", "invalid_timestamp"):
        orig = _original(candidate_id)
        shapes[mode] = _mutate_evidence(candidate_id, mode=mode)
        resp = safe.post(f"/api/v1/journeys/{jid}/plans/{candidate_id}/select")
        shapes[mode]["select_status"] = resp.status_code
        shapes[mode]["select_body"] = resp.text[:160]
        _restore_evidence(candidate_id, orig)
    result["staleness_shapes"] = shapes

    # ---- 3. select a plan, then expire it while the journey is live ------
    sel_ok = safe.post(f"/api/v1/journeys/{jid}/plans/{selected_id}/select")
    result["select_fresh_plan"] = sel_ok.status_code
    if sel_ok.status_code == 200:
        orig_sel = _original(selected_id)
        result["selected_mutation"] = _mutate_evidence(selected_id, mode="expired")
        try:
            from app.services import validate_selected_plan_feasibility

            session = H._session()
            try:
                from app.db.models import Journey as JourneyModel

                jrow = session.get(JourneyModel, jid)
                try:
                    verdict = validate_selected_plan_feasibility(session, jrow)
                    result["selected_plan_revalidation"] = {
                        "raised": False,
                        "passed": getattr(verdict, "passed", None),
                        "failures": list(getattr(verdict, "failures", []) or []),
                    }
                except Exception as exc:  # noqa: BLE001
                    result["selected_plan_revalidation"] = {
                        "raised": True,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            finally:
                session.close()
        except Exception as exc:  # noqa: BLE001
            result["selected_plan_revalidation"] = {"import_error": f"{type(exc).__name__}: {exc}"}

        st = safe.post(f"/api/v1/journeys/{jid}/start")
        result["start_with_stale_selected"] = st.status_code
        result["start_with_stale_body"] = st.text[:200]
        result["journey_status"] = H.journey(jid).get("status")
        exp = safe.get(f"/api/v1/journeys/{jid}/experience")
        result["experience"] = exp.status_code
        if exp.status_code == 200:
            body_text = exp.text
            result["experience_flags_staleness"] = any(
                token in body_text
                for token in ("STALE", "stale", "expired", "RECOMPOSE", "needs_review")
            )
        _restore_evidence(selected_id, orig_sel)

    result["summary"] = {
        "stale_candidate_refused": result.get("stale_candidate_refused"),
        "all_shapes_refused": all(
            v.get("select_status") in (409, 422)
            for k, v in result.get("staleness_shapes", {}).items()
            if isinstance(v, dict) and "select_status" in v
        ),
        "stale_selected_plan_revalidation_raises": result.get(
            "selected_plan_revalidation", {}
        ).get("raised"),
        "journey_still_running_on_expired_evidence": (
            result.get("start_with_stale_selected") == 200
            and result.get("journey_status") == "ACTIVE"
        ),
    }

    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / f"stale_candidates_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

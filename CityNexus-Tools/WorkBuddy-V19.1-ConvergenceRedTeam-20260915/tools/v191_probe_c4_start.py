"""V19.1 probe: does an imported (user-confirmed) C4 reservation strand the journey?

Reproduces the production path end to end:

    POST /journeys/{id}/inbox/import      (STRUCTURED_JSON reservation)
    POST /journeys/{id}/inbox/{d}/confirm -> Commitment(level=C4_Anchored)
    POST /journeys/{id}/plans/generate
    POST /journeys/{id}/plans/{p}/select
    POST /journeys/{id}/start             <- the crash lives here

Usage:  python tools/v191_probe_c4_start.py [A|B]
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"
EVID = LAB / "evidence"

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

import v191_harness as H  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

REF = {"ARRIVAL": "C4R-ARRIVAL", "DEPARTURE": "C4R-DEPARTURE", "MID_TRIP": "C4R-MIDTRIP"}


def _reservation(anchor_role: str, arrival_at: str, semantic_node_key: str | None) -> dict:
    body = {
        "reservation_type": "RAIL",
        "confirmation_ref": REF[anchor_role],
        "origin": {"name": "Shanghai Hongqiao", "code": "SHH"},
        "destination": {"name": "Nexus City", "code": "CNX"},
        "scheduled_departure_at": "2026-10-10T08:00:00+08:00",
        "scheduled_arrival_at": arrival_at,
        "anchor_role": anchor_role,
        "provider_key": "mock-rail",
        "price_amount_minor": 128000,
        "currency": "CNY",
    }
    if semantic_node_key:
        body["semantic_node_key"] = semantic_node_key
    return body


def run_case(anchor_role: str, arrival_at: str, semantic_node_key: str | None = None) -> dict:
    """Full lifecycle for one anchor configuration, with 500s captured not raised."""
    H.reset_demo()
    safe = TestClient(H.main_module.app, raise_server_exceptions=False)
    jid = H.DEMO_JOURNEY_ID
    out: dict = {
        "anchor_role": anchor_role,
        "scheduled_arrival_at": arrival_at,
        "semantic_node_key": semantic_node_key,
    }

    imp = safe.post(
        f"/api/v1/journeys/{jid}/inbox/import",
        json={
            "artifact_type": "STRUCTURED_JSON",
            "payload": {"reservation": _reservation(anchor_role, arrival_at, semantic_node_key)},
        },
    )
    out["import"] = imp.status_code
    if imp.status_code not in (200, 201):
        out["import_body"] = imp.text[:300]
        return out

    conf = safe.post(f"/api/v1/journeys/{jid}/inbox/{imp.json()['id']}/confirm")
    out["confirm"] = conf.status_code
    if conf.status_code != 200:
        out["confirm_body"] = conf.text[:300]
        return out
    commitment = conf.json().get("commitment") or {}
    policy = commitment.get("policy") or {}
    out["commitment_level"] = commitment.get("level")
    out["commitment_status"] = commitment.get("status")
    out["semantic_key"] = policy.get("semantic_key")
    out["semantic_key_is_uuid"] = "-" in str(policy.get("semantic_key") or "")

    gen = safe.post(f"/api/v1/journeys/{jid}/plans/generate", json={})
    out["generate"] = gen.status_code
    plans = safe.get(f"/api/v1/journeys/{jid}/plans").json()
    out["plans"] = len(plans) if isinstance(plans, list) else None

    if not isinstance(plans, list) or not plans:
        return out
    sel = safe.post(f"/api/v1/journeys/{jid}/plans/{plans[0]['id']}/select")
    out["select"] = sel.status_code
    out["select_accepted_infeasible_plan"] = sel.status_code == 200

    st = safe.post(f"/api/v1/journeys/{jid}/start")
    out["start"] = st.status_code
    out["start_body"] = st.text[:200]
    jr = safe.get(f"/api/v1/journeys/{jid}")
    out["journey_status_after"] = jr.json().get("status") if jr.status_code == 200 else None
    out["journey_stranded"] = out["start"] >= 500
    out["commitment_survived"] = len(H.commitment_rows()) >= 1

    # GET /twin on the same (still PLANNED) journey — does the same path crash?
    tw = safe.get(f"/api/v1/journeys/{jid}/twin")
    out["twin"] = tw.status_code
    return out


def crash_frames(anchor_role: str = "ARRIVAL") -> dict:
    """Capture the exact frame chain that produces the 500."""
    H.reset_demo()
    jid = H.DEMO_JOURNEY_ID
    imp = H.inbox_import(jid, _reservation(anchor_role, "2026-10-10T12:30:00+08:00", None))
    H.inbox_confirm(jid, imp.json()["id"])
    H.generate_plans()
    H.select_plan(jid, H.list_plans()[0]["id"])
    try:
        H.client.post(f"/api/v1/journeys/{jid}/start")
    except Exception:  # noqa: BLE001
        tb = traceback.format_exc()
        frames = [
            line.strip()
            for line in tb.splitlines()
            if ("app\\" in line or "app/" in line or line.strip().startswith("File "))
            and "site-packages" not in line
        ]
        return {
            "frames": frames,
            "exception": tb.strip().splitlines()[-1],
            "key_error": next(
                (ln.strip() for ln in tb.splitlines() if ln.strip().startswith("KeyError:")),
                None,
            ),
        }
    return {"frames": [], "exception": None, "key_error": None}


def main() -> int:
    cases = [
        ("ARRIVAL", "2026-10-10T12:30:00+08:00", None),
        ("DEPARTURE", "2026-10-10T12:30:00+08:00", None),
        ("MID_TRIP", "2026-10-10T12:30:00+08:00", "place-old-town"),
        ("MID_TRIP", "2026-10-10T12:30:00+08:00", "place-riverside-museum"),
        # ARRIVAL that lands BEFORE the first planned activity -> filtered out
        ("ARRIVAL", "2026-10-10T07:00:00+08:00", None),
        # no reservation at all: control
        (None, None, None),
    ]
    result: dict = {"snapshot": LABEL, "cases": []}
    for role, arrival, node in cases:
        if role is None:
            H.reset_demo()
            safe = TestClient(H.main_module.app, raise_server_exceptions=False)
            jid = H.DEMO_JOURNEY_ID
            gen = safe.post(f"/api/v1/journeys/{jid}/plans/generate", json={})
            plans = safe.get(f"/api/v1/journeys/{jid}/plans").json()
            sel = safe.post(f"/api/v1/journeys/{jid}/plans/{plans[0]['id']}/select")
            st = safe.post(f"/api/v1/journeys/{jid}/start")
            result["cases"].append(
                {
                    "anchor_role": None,
                    "note": "control: no reservation imported",
                    "generate": gen.status_code,
                    "plans": len(plans),
                    "select": sel.status_code,
                    "start": st.status_code,
                    "journey_status_after": safe.get(f"/api/v1/journeys/{jid}").json().get("status"),
                }
            )
            continue
        try:
            result["cases"].append(run_case(role, arrival, node))
        except Exception as exc:  # noqa: BLE001
            result["cases"].append(
                {"anchor_role": role, "probe_error": f"{type(exc).__name__}: {exc}"}
            )

    result["crash_frames"] = crash_frames("ARRIVAL")
    result["summary"] = {
        "stranded_roles": [
            c.get("anchor_role") for c in result["cases"] if c.get("journey_stranded")
        ],
        "any_stranded": any(c.get("journey_stranded") for c in result["cases"]),
    }

    out = EVID / f"c4_start_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str)[:6000])
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

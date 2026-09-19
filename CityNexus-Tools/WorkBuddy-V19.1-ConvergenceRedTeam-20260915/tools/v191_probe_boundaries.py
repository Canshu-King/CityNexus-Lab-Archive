"""V19.1 probe: are numeric limits and time windows MEANINGFULLY ENFORCED?

Extraction (canonicalization) is measured separately.  This probe asks the other
half of the question: once a capability carries a numeric/parametric limit, does
the feasibility gate actually act on it?

Every case is driven through the real HTTP surface:
    POST /journeys/{id}/capabilities/confirm   -> declare the limit
    POST /journeys/{id}/plans/generate         -> ask for a plan

Usage:  python tools/v191_probe_boundaries.py [A|B]
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

# Walking limits: every value the task book asks about.
WALKING_CASES = [
    ("zero", {"max_m": 0}),
    ("one", {"max_m": 1}),
    ("100", {"max_m": 100}),
    ("499", {"max_m": 499}),
    ("500", {"max_m": 500}),
    ("501", {"max_m": 501}),
    ("1000", {"max_m": 1000}),
    ("10000", {"max_m": 10000}),
    ("negative", {"max_m": -1}),
    ("huge", {"max_m": 10**12}),
    ("string_500", {"max_m": "500"}),
    ("string_500m", {"max_m": "500m"}),
    ("null", {"max_m": None}),
    ("missing_key", {}),
    ("float", {"max_m": 500.7}),
]

CONTINUOUS_CASES = [
    ("zero_min", {"max_min": 0}),
    ("one_min", {"max_min": 1}),
    ("30_min", {"max_min": 30}),
    ("negative", {"max_min": -10}),
    ("string", {"max_min": "30"}),
    ("missing", {}),
]

DAILY_CASES = [
    ("1000_m", {"max_m": 1000}),
    ("zero", {"max_m": 0}),
    ("negative", {"max_m": -5}),
    ("missing", {}),
]

WINDOW_CASES = [
    ("normal_12_14", {"start": "12:00", "end": "14:00"}),
    ("narrow_12_1215", {"start": "12:00", "end": "12:15"}),
    ("whole_day", {"start": "00:00", "end": "23:59"}),
    ("end_before_start", {"start": "14:00", "end": "12:00"}),
    ("equal", {"start": "12:00", "end": "12:00"}),
    ("cross_midnight", {"start": "22:00", "end": "02:00"}),
    ("minutes_ints", {"start": 720, "end": 840}),
    ("out_of_range", {"start": "25:00", "end": "26:00"}),
    ("malformed", {"start": "noon", "end": "2pm"}),
    ("missing_both", {}),
    ("only_start", {"start": "12:00"}),
    ("iso_datetimes", {"start": "2026-10-10T12:00:00+08:00", "end": "2026-10-10T14:00:00+08:00"}),
]

BREAK_CASES = [
    ("every_30", {"max_min": 30}),
    ("every_0", {"max_min": 0}),
    ("every_negative", {"max_min": -30}),
    ("every_string", {"max_min": "45"}),
    ("every_wrong_key", {"every_min": 30}),
    ("missing", {}),
]

# Fail-open / fail-closed symmetry: the same "we have no evidence" situation,
# evaluated for an accessibility code and for a stroller/luggage code.
EVIDENCE_SYMMETRY_CASES = [
    ("stroller_metadata_absent", "STROLLER", None),
    ("stroller_explicitly_denied", "STROLLER", {"stroller_accessible": False}),
    ("stroller_explicitly_allowed", "STROLLER", {"stroller_accessible": True}),
    ("luggage_metadata_absent", "LARGE_LUGGAGE", None),
    ("luggage_explicitly_denied", "LARGE_LUGGAGE", {"luggage_accessible": False}),
    ("luggage_explicitly_allowed", "LARGE_LUGGAGE", {"luggage_accessible": True}),
    ("step_free_metadata_absent", "STEP_FREE_REQUIRED", None),
    ("step_free_explicitly_denied", "STEP_FREE_REQUIRED", {"step_free": False}),
    ("step_free_explicitly_allowed", "STEP_FREE_REQUIRED", {"step_free": True}),
]


def _set_place_metadata(accessibility: dict | None) -> int:
    """Write (or clear) accessibility metadata on every place in the snapshot DB."""
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
        return len(rows)


def _probe(code: str, params: dict, place_metadata: dict | None = None) -> dict:
    H.reset_demo()
    _set_place_metadata(place_metadata)
    declared = H.confirm_journey_capabilities([H.capability(code, "HARD", params=params)])
    persisted = [c for c in H.capability_rows("JOURNEY") if c.get("code") == code]
    gen_status, body = H.generate_plans()
    out = {
        "params_sent": params,
        "place_metadata": place_metadata,
        "declare_status": declared.status_code,
        "persisted_params": persisted[0].get("params") if persisted else None,
        "persisted": bool(persisted),
        "generate_status": gen_status,
        "plans": len(H.list_plans()),
        "gate_blocked": gen_status != 201,
        "gate_message": (
            (body or {}).get("error", {}).get("message") if isinstance(body, dict) else None
        ),
    }
    _set_place_metadata(None)
    return out


def _section(code: str, cases: list[tuple[str, dict]]) -> dict:
    out: dict = {}
    for label, params in cases:
        try:
            out[label] = _probe(code, params)
        except Exception as exc:  # noqa: BLE001
            out[label] = {"probe_error": f"{type(exc).__name__}: {exc}"}
    out["_summary"] = {
        "total": len(cases),
        "blocked": sum(1 for v in out.values() if isinstance(v, dict) and v.get("gate_blocked")),
        "accepted": sum(
            1
            for v in out.values()
            if isinstance(v, dict) and v.get("generate_status") == 201
        ),
    }
    return out


def _control() -> dict:
    """No capability declared: the gate must accept."""
    H.reset_demo()
    status, _ = H.generate_plans()
    return {"generate_status": status, "plans": len(H.list_plans())}


def _evidence_symmetry() -> dict:
    """Same question — 'is there evidence?' — asked of accessibility and of stroller/luggage."""
    out: dict = {}
    for label, code, metadata in EVIDENCE_SYMMETRY_CASES:
        try:
            out[label] = _probe(code, {}, place_metadata=metadata)
        except Exception as exc:  # noqa: BLE001
            out[label] = {"probe_error": f"{type(exc).__name__}: {exc}"}
    return out


def main() -> int:
    result: dict = {"snapshot": LABEL, "control": _control()}
    for name, code, cases in (
        ("max_walking_per_leg_m", "MAX_WALKING_PER_LEG_M", WALKING_CASES),
        ("max_continuous_walking_min", "MAX_CONTINUOUS_WALKING_MIN", CONTINUOUS_CASES),
        ("max_daily_walking_m", "MAX_DAILY_WALKING_M", DAILY_CASES),
        ("midday_rest_window", "MIDDAY_REST_WINDOW", WINDOW_CASES),
        ("infant_nap_window", "INFANT_NAP_WINDOW", WINDOW_CASES),
        ("rest_every_min", "REST_EVERY_MIN", BREAK_CASES),
        ("toilet_break_every_min", "TOILET_BREAK_EVERY_MIN", BREAK_CASES),
    ):
        result[name] = _section(code, cases)
    result["evidence_symmetry"] = _evidence_symmetry()

    out = EVID / f"boundaries_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    for name, value in result.items():
        if name in ("snapshot", "control"):
            print(f"{name}: {json.dumps(value, ensure_ascii=False)}")
            continue
        if name == "evidence_symmetry":
            print("\n=== evidence_symmetry (fail-open vs fail-closed) ===")
            for label, row in value.items():
                print(
                    f"  {label:<28} gen={row.get('generate_status')} "
                    f"blocked={row.get('gate_blocked')} plans={row.get('plans')}"
                )
            continue
        print(f"\n=== {name} === {json.dumps(value.get('_summary'), ensure_ascii=False)}")
        for label, row in value.items():
            if label.startswith("_"):
                continue
            print(
                f"  {label:<20} declare={row.get('declare_status')} "
                f"persisted={row.get('persisted')} gen={row.get('generate_status')} "
                f"plans={row.get('plans')} params={json.dumps(row.get('persisted_params'), ensure_ascii=False)}"
            )
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

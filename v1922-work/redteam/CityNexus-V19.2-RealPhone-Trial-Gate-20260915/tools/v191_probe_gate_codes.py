"""V19.1 probe: what failure codes does the gate actually compute, and where do they go?

The public API collapses every infeasibility into one opaque 422.  This probe taps
`evaluate_feasibility` inside the process to see the real codes, then compares them
with what the client receives.

Usage:  python tools/v191_probe_gate_codes.py [A|B]
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

CAPTURED: list[dict] = []


def _install_tap() -> None:
    """Record every FeasibilityResult the gate produces, without changing it."""
    import app.services as services
    from app.replanning import feasibility

    for module, attr in ((services, "evaluate_feasibility"),):
        original = getattr(module, attr)

        def wrapper(context, activities, _orig=original):
            result = _orig(context, activities)
            failures = list(getattr(result, "failures", []) or [])
            codes = sorted(
                {
                    getattr(c, "rule_code", None) or getattr(c, "category", None)
                    for c in getattr(context, "constraints", [])
                }
                - {None}
            )
            CAPTURED.append(
                {
                    "feasible": bool(getattr(result, "feasible", None)),
                    "failures": failures,
                    "constraint_codes": codes,
                }
            )
            return result

        setattr(module, attr, wrapper)

    # feasibility.evaluate_feasibility is imported by name into services, so the
    # services binding is the one the generation path calls.
    _ = feasibility


def _case(code: str | None, params: dict | None) -> dict:
    CAPTURED.clear()
    H.reset_demo()
    declared = None
    if code:
        declared = H.confirm_journey_capabilities([H.capability(code, "HARD", params=params or {})]).status_code
    status, body = H.generate_plans()
    last = CAPTURED[-1] if CAPTURED else {}
    all_failures = sorted({f for c in CAPTURED for f in c["failures"]})
    return {
        "declared": declared,
        "generate_status": status,
        "plans": len(H.list_plans()),
        "api_message": (
            (body or {}).get("error", {}).get("message") if isinstance(body, dict) else None
        ),
        "gate_calls": len(CAPTURED),
        "gate_feasible_any": any(c["feasible"] for c in CAPTURED) if CAPTURED else None,
        "gate_failures_last": last.get("failures"),
        "gate_failures_all": all_failures,
        "gate_constraint_codes": last.get("constraint_codes"),
    }


CASES = [
    ("control_no_capability", None, None),
    ("walk_500", "MAX_WALKING_PER_LEG_M", {"max_m": 500}),
    ("walk_huge", "MAX_WALKING_PER_LEG_M", {"max_m": 10**12}),
    ("walk_missing", "MAX_WALKING_PER_LEG_M", {}),
    ("rest_12_14", "MIDDAY_REST_WINDOW", {"start": "12:00", "end": "14:00"}),
    ("rest_whole_day", "MIDDAY_REST_WINDOW", {"start": "00:00", "end": "23:59"}),
    ("rest_invalid", "MIDDAY_REST_WINDOW", {"start": "14:00", "end": "12:00"}),
    ("step_free_no_evidence", "STEP_FREE_REQUIRED", {}),
    ("avoid_stairs_no_evidence", "AVOID_STAIRS", {}),
    ("stroller", "STROLLER", {}),
    ("large_luggage", "LARGE_LUGGAGE", {}),
    ("rest_every_30", "REST_EVERY_MIN", {"every_min": 30}),
]


def main() -> int:
    _install_tap()
    result = {"snapshot": LABEL, "cases": {}}
    for label, code, params in CASES:
        try:
            result["cases"][label] = _case(code, params)
        except Exception as exc:  # noqa: BLE001
            result["cases"][label] = {"probe_error": f"{type(exc).__name__}: {exc}"}

    # Do the computed codes ever reach the client?
    result["client_visibility"] = {
        "distinct_api_messages": sorted(
            {
                c.get("api_message")
                for c in result["cases"].values()
                if c.get("api_message")
            }
        ),
        "distinct_gate_codes": sorted(
            {f for c in result["cases"].values() for f in (c.get("gate_failures_all") or [])}
        ),
    }

    out = EVID / f"gate_codes_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    for label, row in result["cases"].items():
        print(f"\n### {label}")
        print(f"    gen={row.get('generate_status')} plans={row.get('plans')}")
        print(f"    api_message: {row.get('api_message')}")
        print(f"    gate_failures_all: {json.dumps(row.get('gate_failures_all'), ensure_ascii=False)}")
    print("\n=== client visibility ===")
    print(json.dumps(result["client_visibility"], ensure_ascii=False, indent=1))
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

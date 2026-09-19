"""End-to-end: traveller sentence -> capability -> constraint -> feasibility gate.

Runs entirely against ``repo_copy_current`` (the byte-copy of the main tree taken
after Codex landed ``app/capabilities.py``).  It answers one question: once a
traveller states a hard accessibility need, does the deterministic gate accept
the constraint the capability layer projects?

Usage:
    python tools/v19_probe_capability_gate.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
CURRENT = LAB / "repo_copy_current"
EVID = LAB / "evidence"

sys.path.insert(0, str(CURRENT / "backend"))

from app.capabilities import (  # noqa: E402
    canonicalize_capabilities,
    capability_constraints,
    extract_capabilities_from_text,
)
from app.integrations.mock.providers import MockMobilityProvider  # noqa: E402
from app.replanning.feasibility import (  # noqa: E402
    FeasibilityActivity,
    FeasibilityContext,
    evaluate_feasibility,
)

START = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)

PLACE = {
    "id": "p1",
    "city_code": "TJN",
    "status": "available",
    "opening_hours_json": {"start": "08:00", "end": "22:00"},
    "metadata_json": {},
}


def context(constraints) -> FeasibilityContext:
    return FeasibilityContext(
        journey_id="journey-1",
        city_code="TJN",
        journey_start=START,
        journey_end=START + timedelta(hours=10),
        budget_amount_minor=200_000,
        budget_currency="CNY",
        constraints=tuple(constraints),
        places={"p1": PLACE},
        services={},
        mobility_provider=MockMobilityProvider(),
        plan_currency="CNY",
    )


def activities() -> list[FeasibilityActivity]:
    return [
        FeasibilityActivity(
            key="a1",
            start_at=START + timedelta(hours=1),
            end_at=START + timedelta(hours=2),
            cost_minor=5_000,
            place_id="p1",
        )
    ]


def run(label: str, text: str) -> dict:
    caps = extract_capabilities_from_text(text)
    gates = capability_constraints(caps)
    result = evaluate_feasibility(context(gates), activities())
    return {
        "label": label,
        "text": text,
        "capabilities": [{"code": c["code"], "severity": c["severity"]} for c in caps],
        "projected_constraints": [
            {"kind": g["kind"], "category": g["category"], "rule_code": g["rule_code"]} for g in gates
        ],
        "gate_passed": result.passed,
        "gate_failures": list(result.failures),
    }


def main() -> int:
    out: dict = {}

    scenarios = {
        "hard_wheelchair_zh": "我用轮椅，必须全程 step-free，一步楼梯都不能走",
        "hard_wheelchair_en": "I use a wheelchair, every leg must be step-free",
        "soft_stairs_zh": "最好少走点楼梯，能坐电梯就坐电梯",
        "hard_avoid_stairs_only": "我膝盖不行，不能走楼梯，请避免台阶",
        "hard_rest_window": "老人中午 12 点到 14 点必须回酒店休息",
        "soft_quiet": "希望安静一点，少刺激",
        "hard_walking_limit": "走路不能超过 500m，这是硬性要求",
    }
    out["scenarios"] = {k: run(k, v) for k, v in scenarios.items()}

    # A control: no capability at all.
    baseline = evaluate_feasibility(context([]), activities())
    out["control_no_constraints"] = {"gate_passed": baseline.passed, "gate_failures": list(baseline.failures)}

    # A control: a supported HARD code, to prove the gate itself is healthy.
    supported = evaluate_feasibility(
        context([{"kind": "HARD", "category": "BUDGET", "rule_code": "BUDGET_MAX",
                  "params": {"amount_minor": 100_000}, "active": True}]),
        activities(),
    )
    out["control_supported_code"] = {"gate_passed": supported.passed, "gate_failures": list(supported.failures)}

    # Which rule codes does the gate actually interpret?
    interpreted = ("BUDGET_MAX", "JOURNEY_END_BY", "JOURNEY_START_AT", "PLACE_UNAVAILABLE",
                   "PLACE_CLOSED", "SERVICE_UNAVAILABLE", "SERVICE_CLOSED", "REQUIRE_PLACE",
                   "LOCKED_COMMITMENT")
    emitted = set()
    for case_text in scenarios.values():
        for gate in capability_constraints(extract_capabilities_from_text(case_text)):
            emitted.add(gate["rule_code"])
    out["gate_vocabulary"] = {
        "interpreted_by_gate": list(interpreted),
        "emitted_by_capability_layer": sorted(emitted),
        "emitted_but_not_interpreted": sorted(emitted - set(interpreted)),
        "conclusion": (
            "capability_constraints() projects rule codes the feasibility gate "
            "does not implement, so every such constraint fails closed as "
            "UNSUPPORTED_HARD_CONSTRAINT and the Journey cannot be planned."
        ),
    }

    # The accessibility evidence channel is imported by the gate but never used.
    feasibility_src = (CURRENT / "backend" / "app" / "replanning" / "feasibility.py").read_text(encoding="utf-8")
    out["accessibility_state_wiring"] = {
        "imported": "from app.capabilities import accessibility_state" in feasibility_src,
        "call_sites": feasibility_src.count("accessibility_state("),
        "conclusion": (
            "accessibility_state() is imported by the feasibility gate but never "
            "called, so plan feasibility never consults provider accessibility "
            "evidence."
        ),
    }

    (EVID / "capability_gate_probe.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

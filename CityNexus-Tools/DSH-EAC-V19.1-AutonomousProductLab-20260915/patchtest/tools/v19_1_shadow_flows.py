"""Run eight deterministic shadow traveler flows against the isolated V19 backend."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "lab" / "runtime" / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("CITYNEXUS_DATABASE_URL", "sqlite:///./v19_1_flows.db")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.models import Place  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
EVIDENCE = ROOT / "evidence" / "shadow_e2e_results.jsonl"


def set_place_tags(place_id: str, tags: dict[str, object]) -> None:
    with SessionLocal() as session:
        place = session.get(Place, place_id)
        if place is None:
            raise SystemExit(f"place not found: {place_id}")
        existing = json.loads(place.metadata_json or "{}")
        if not isinstance(existing, dict):
            existing = {}
        existing["tags"] = tags
        place.metadata_json = json.dumps(existing, ensure_ascii=False)
        place.tags_json = json.dumps([], ensure_ascii=False)
        session.commit()


def reset_demo() -> dict[str, str]:
    response = client.post("/api/v1/demo/reset")
    response.raise_for_status()
    return response.json()


def confirm_capabilities(journey_id: str, capabilities: list[dict[str, object]]) -> dict:
    response = client.post(f"/api/v1/journeys/{journey_id}/capabilities/confirm", json=capabilities)
    try:
        body = response.json()
    except Exception:
        body = response.text
    return {"status_code": response.status_code, "body": body}


def generate_plan(journey_id: str) -> dict:
    response = client.post(f"/api/v1/journeys/{journey_id}/plans/generate", json={"candidate_count": 1})
    if response.status_code != 201:
        return {"status_code": response.status_code, "body": response.text}
    plans = response.json()
    return {"status_code": response.status_code, "plan_id": plans[0]["id"], "plan_count": len(plans)}


def plan_impact(journey_id: str, plan_id: str | None) -> dict:
    params = {"plan_version_id": plan_id} if plan_id else None
    response = client.get(f"/api/v1/journeys/{journey_id}/capability-plan-impact", params=params)
    try:
        body = response.json()
    except Exception:
        body = response.text
    return {"status_code": response.status_code, "body": body}


def provider_evidence(place_id: str) -> dict:
    response = client.get(f"/api/v1/places/{place_id}/accessibility-evidence")
    try:
        body = response.json()
    except Exception:
        body = response.text
    return {"status_code": response.status_code, "body": body}


def cap(code: str, klass: str, severity: str, params: dict[str, object], scope: str = "JOURNEY") -> dict[str, object]:
    return {
        "code": code,
        "class": klass,
        "severity": severity,
        "params": params,
        "scope": scope,
        "source": "USER_CONFIRMED",
        "provenance": "USER_CONFIRMED",
        "explicit": True,
        "active": True,
        "confirmed": True,
    }


FLOWS = [
    {
        "id": "A_elderly_walking_rest",
        "label": "A elderly + walking limit + midday rest",
        "place_tags": None,
        "capabilities": [
            cap("MAX_WALKING_PER_LEG_M", "PHYSICAL_LIMIT", "HARD", {"max_m": 500}),
            cap("MIDDAY_REST_WINDOW", "CARE_REQUIREMENT", "HARD", {"start": "12:00", "end": "14:00"}),
        ],
        "expect": "HARD walking and rest should be evaluated by the gate; unknown provider evidence must remain visible.",
    },
    {
        "id": "B_wheelchair_verified_place",
        "label": "B wheelchair + verified place",
        "place_tags": {"wheelchair": "yes", "entrance:wheelchair": "yes"},
        "capabilities": [cap("STEP_FREE_REQUIRED", "HARD_ACCESSIBILITY_NEED", "HARD", {"requirement": "step_free"})],
        "expect": "Explicit provider tags may verify the place; route-level step-free evidence still remains NEEDS_LIVE_EVIDENCE.",
    },
    {
        "id": "C_wheelchair_unknown_place",
        "label": "C wheelchair + unknown place",
        "place_tags": {"name": "Unknown venue"},
        "capabilities": [cap("STEP_FREE_REQUIRED", "HARD_ACCESSIBILITY_NEED", "HARD", {"requirement": "step_free"})],
        "expect": "No tags must produce ACCESSIBILITY_UNVERIFIED / NEEDS_LIVE_EVIDENCE, never accessible.",
    },
    {
        "id": "D_wheelchair_conflict_place",
        "label": "D wheelchair + conflict place",
        "place_tags": {"wheelchair": "no", "highway": "steps", "step_count": "12"},
        "capabilities": [cap("STEP_FREE_REQUIRED", "HARD_ACCESSIBILITY_NEED", "HARD", {"requirement": "step_free"})],
        "expect": "Explicit conflict should be rejected/highlighted, never softened to preserved.",
    },
    {
        "id": "E_infant_nap_stroller",
        "label": "E infant + nap + stroller",
        "place_tags": {"stroller_accessible": "unknown"},
        "capabilities": [
            cap("INFANT_NAP_WINDOW", "CARE_REQUIREMENT", "HARD", {"start": "13:00", "end": "15:00"}),
            cap("STROLLER", "TRIP_CONTEXT", "STRONG", {"present": True}),
            cap("REST_EVERY_MIN", "CARE_REQUIREMENT", "STRONG", {"max_min": 60}),
        ],
        "expect": "Care window may be unsatisfied in a generated plan; stroller facility evidence remains unknown unless proven.",
    },
    {
        "id": "F_large_luggage",
        "label": "F large luggage",
        "place_tags": {"luggage_accessible": "unknown"},
        "capabilities": [
            cap("LARGE_LUGGAGE", "TRIP_CONTEXT", "STRONG", {"present": True}),
            cap("MAX_WALKING_PER_LEG_M", "PHYSICAL_LIMIT", "STRONG", {"max_m": 600}),
        ],
        "expect": "Luggage context should not fabricate accessibility; unknown facility evidence stays unknown.",
    },
    {
        "id": "G_normal_soft_preference",
        "label": "G normal soft preference",
        "place_tags": {"name": "Quiet museum"},
        "capabilities": [
            cap("QUIET_ENVIRONMENT", "SOFT_PREFERENCE", "SOFT", {"preferred": True}),
            cap("INDOOR_PREFERRED", "SOFT_PREFERENCE", "SOFT", {"preferred": True}),
        ],
        "expect": "Soft preference must remain ranking/explanation context, not a hard gate or accessibility claim.",
    },
    {
        "id": "H_conflicting_family_needs",
        "label": "H conflicting family needs",
        "place_tags": {"wheelchair": "limited", "stroller_accessible": "unknown", "step_count": "3"},
        "capabilities": [
            cap("STEP_FREE_REQUIRED", "HARD_ACCESSIBILITY_NEED", "HARD", {"requirement": "step_free"}),
            cap("AVOID_STAIRS", "HARD_ACCESSIBILITY_NEED", "HARD", {"avoid": True}),
            cap("STROLLER", "TRIP_CONTEXT", "STRONG", {"present": True}),
            cap("INFANT_NAP_WINDOW", "CARE_REQUIREMENT", "HARD", {"start": "13:00", "end": "14:30"}),
        ],
        "expect": "Conflicting hard accessibility plus care needs must be surfaced separately and never collapsed into one green pass.",
    },
]


def run_flow(flow: dict[str, object]) -> dict[str, object]:
    demo = reset_demo()
    traveler_id = demo["traveler_id"]
    journey_id = demo["journey_id"]
    place_id = "place-riverside-museum"
    if flow.get("place_tags") is not None:
        set_place_tags(place_id, flow["place_tags"])  # type: ignore[arg-type]
    # Generate the baseline plan first so the impact endpoint can evaluate the
    # persisted activities against the newly confirmed capabilities.  A hard
    # capability may make the baseline infeasible; that is a valid shadow result.
    generation = generate_plan(journey_id)
    confirmation = confirm_capabilities(journey_id, flow["capabilities"])  # type: ignore[arg-type]
    impact = plan_impact(journey_id, generation.get("plan_id"))
    evidence = provider_evidence(place_id)
    impact_body = impact.get("body") if isinstance(impact, dict) else {}
    impacts = impact_body.get("impacts") if isinstance(impact_body, dict) else None
    unknown_count = len(impacts.get("unknown", [])) if isinstance(impacts, dict) else 0
    rejected_count = len(impacts.get("rejected", [])) if isinstance(impacts, dict) else 0
    if confirmation.get("status_code") != 200:
        status = "BUG"
    elif generation.get("status_code") != 201:
        status = "BLOCKED"
    elif not isinstance(impact_body, dict) or impact_body.get("status") == "CONTRACT_NOT_AVAILABLE":
        status = "CONTRACT_GAP"
    elif impact_body.get("status") == "FAIL" and rejected_count and unknown_count:
        status = "FAIL_EXPECTED_CONFLICT_WITH_GAP"
    elif impact_body.get("status") == "FAIL" and rejected_count:
        status = "FAIL_EXPECTED_CONFLICT"
    elif impact_body.get("status") == "FAIL" and unknown_count:
        status = "NEEDS_EVIDENCE"
    elif impact_body.get("status") == "FAIL":
        status = "BUG"
    elif unknown_count:
        status = "NEEDS_EVIDENCE"
    else:
        status = "PASS"
    provider_body = evidence.get("body") if isinstance(evidence, dict) else {}
    return {
        "flow_id": flow["id"],
        "label": flow["label"],
        "traveler_id": traveler_id,
        "journey_id": journey_id,
        "place_id": place_id,
        "confirmed": confirmation,
        "generation": generation,
        "impact_status": impact_body.get("status") if isinstance(impact_body, dict) else None,
        "impact_unknown_count": unknown_count,
        "impact_rejected_count": rejected_count,
        "provider_overall_state": provider_body.get("overall_state") if isinstance(provider_body, dict) else None,
        "provider_items": len(provider_body.get("items", [])) if isinstance(provider_body, dict) else 0,
        "status": status,
        "expectation": flow["expect"],
    }


def main() -> None:
    lines = []
    for flow in FLOWS:
        result = run_flow(flow)
        lines.append(result)
        print(f"{result['flow_id']}: {result['status']} ({result['impact_status']})")
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in lines) + "\n", encoding="utf-8")
    print(f"wrote {EVIDENCE}")


if __name__ == "__main__":
    main()

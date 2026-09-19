from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.capabilities import (
    accessibility_state,
    canonicalize_capabilities,
    extract_capabilities_from_text,
)
from app.main import app
from app.replanning.feasibility import build_context, evaluate_feasibility
from app.replanning.provider_snapshots import MobilitySnapshot, TravelEstimateFact


client = TestClient(app)


def test_capability_interpretation_preserves_hard_need_and_rejects_negation():
    items = extract_capabilities_from_text("I must use step-free routes and walk less than 500 m per leg")
    assert {item["code"] for item in items} == {"STEP_FREE_REQUIRED", "MAX_WALKING_PER_LEG_M"}
    assert all(item["severity"] == "HARD" for item in items)
    assert extract_capabilities_from_text("I used to use a wheelchair, not now") == ()


def test_unknown_accessibility_is_not_accessible():
    assert accessibility_state({}) == "ACCESSIBILITY_UNVERIFIED"
    assert accessibility_state({"step_free": True}) == "ACCESSIBILITY_VERIFIED"
    assert accessibility_state({"step_free": False}) == "ACCESSIBILITY_CONFLICT"
    item = canonicalize_capabilities(
        [{"code": "STEP_FREE_REQUIRED", "class": "SOFT_PREFERENCE", "severity": "HARD", "params": {}}]
    )[0]
    assert item["class"] == "HARD_ACCESSIBILITY_NEED"
    assert item["severity"] == "HARD"


def test_feasibility_blocks_unknown_and_conflicting_step_free_evidence():
    start = datetime(2026, 9, 15, 9, tzinfo=timezone.utc)
    journey = SimpleNamespace(
        id="j1", city_code="CNX", start_at=start, end_at=datetime(2026, 9, 15, 18, tzinfo=timezone.utc),
        budget_amount_minor=10000, budget_currency="CNY",
    )
    activity = SimpleNamespace(
        key="p1", place_id="p1", city_service_id=None, start_at=start, end_at=datetime(2026, 9, 15, 10, tzinfo=timezone.utc),
        cost_minor=100, currency="CNY", locked=False,
    )
    constraint = {"kind": "HARD", "category": "HARD_ACCESSIBILITY_NEED", "rule_code": "STEP_FREE_REQUIRED", "params": {}, "active": True}
    provider = MobilitySnapshot(facts={}, source_provider_key="frozen", captured_at=start.isoformat())
    context = build_context(journey, [constraint], {"p1": {"id": "p1", "city_code": "CNX", "opening_hours": {"open": "08:00", "close": "20:00"}}}, {}, mobility_provider=provider)
    result = evaluate_feasibility(context, [activity])
    assert not result.passed
    assert "NEEDS_LIVE_EVIDENCE:p1" in result.failures


def test_capability_confirmation_endpoint_materializes_twin_evidence():
    ids = client.post("/api/v1/demo/reset").json()
    capability = [{"code": "STEP_FREE_REQUIRED", "class": "HARD_ACCESSIBILITY_NEED", "severity": "HARD", "params": {}}]
    assert client.put(f"/api/v1/travelers/{ids['traveler_id']}/capabilities", json=capability).status_code == 409
    response = client.post(f"/api/v1/travelers/{ids['traveler_id']}/capabilities/confirm", json=capability)
    assert response.status_code == 200
    twin = response.json()["traveler_twin"]
    assert twin["explicit_capabilities"][0]["code"] == "STEP_FREE_REQUIRED"
    assert twin["explicit_capabilities"][0]["confirmed"] is True

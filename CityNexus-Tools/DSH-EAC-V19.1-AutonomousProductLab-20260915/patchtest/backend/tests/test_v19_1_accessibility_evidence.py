from __future__ import annotations

import json
from pathlib import Path

from app.integrations.accessibility.osm import evidence_from_osm_tags

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "accessibility" / "evidence_cases.json").read_text(
        encoding="utf-8"
    )
)


def _facts(case):
    return evidence_from_osm_tags(
        case["tags"],
        provider=case["provider"],
        source_key=case["source_key"],
        city_code=case["city_code"],
        captured_at="2026-09-15T12:00:00+08:00",
    )


def test_frozen_accessibility_fixtures_are_conservative() -> None:
    for case in FIXTURES:
        facts = _facts(case)
        assert [fact.state for fact in facts] == case["expected_states"], case["id"]
        assert [fact.code for fact in facts] == case["expected_codes"], case["id"]
        for fact in facts:
            assert fact.provider == case["provider"]
            assert fact.source_key == case["source_key"]
            assert fact.captured_at == "2026-09-15T12:00:00+08:00"
            assert "raw_key" in fact.provenance


def test_unknown_never_becomes_verified() -> None:
    facts = evidence_from_osm_tags({}, source_key="overpass:node/0", city_code="CNX-DEMO")
    assert len(facts) == 1
    assert facts[0].state == "NEEDS_LIVE_EVIDENCE"
    assert facts[0].raw_key is None
    assert "unknown" in facts[0].summary.lower()


def test_ramp_and_elevator_are_not_route_verification() -> None:
    facts = evidence_from_osm_tags(
        {"ramp": "yes", "elevator": "yes", "highway": "footway"},
        source_key="overpass:way/9",
        city_code="CNX-DEMO",
    )
    assert {fact.code for fact in facts} == {"RAMP_PRESENT", "ELEVATOR_PRESENT"}
    assert all(fact.state == "ACCESSIBILITY_UNVERIFIED" for fact in facts)


def test_wheelchair_yes_with_steps_is_conflict_not_verified_route() -> None:
    facts = evidence_from_osm_tags(
        {"wheelchair": "yes", "highway": "steps"},
        source_key="overpass:node/8",
        city_code="CNX-DEMO",
    )
    states = {fact.state for fact in facts}
    assert "ACCESSIBILITY_CONFLICT" in states
    assert any(fact.code == "CONFLICTING_TAGS" for fact in facts)


def test_place_and_journey_accessibility_endpoints_are_evidence_negative() -> None:
    import json

    from fastapi.testclient import TestClient

    from app.db.models import Place
    from app.db.session import SessionLocal
    from app.main import app

    client = TestClient(app)
    demo = client.post("/api/v1/demo/reset").json()
    journey_id = demo["journey_id"]

    with SessionLocal() as session:
        place = session.query(Place).first()
        assert place is not None
        place.metadata_json = json.dumps({"tags": {"wheelchair": "yes"}}, ensure_ascii=False)
        place.tags_json = json.dumps([], ensure_ascii=False)
        place_id = place.id
        session.commit()

    verified = client.get(f"/api/v1/places/{place_id}/accessibility-evidence")
    assert verified.status_code == 200, verified.text
    body = verified.json()
    assert body["overall_state"] == "ACCESSIBILITY_VERIFIED"
    assert body["items"][0]["raw"] == {"key": "wheelchair", "value": "yes"}

    with SessionLocal() as session:
        place = session.get(Place, place_id)
        assert place is not None
        place.metadata_json = json.dumps({"tags": {"name": "Unknown museum"}}, ensure_ascii=False)
        session.commit()

    unknown = client.get(f"/api/v1/places/{place_id}/accessibility-evidence")
    assert unknown.status_code == 200, unknown.text
    assert unknown.json()["overall_state"] == "NEEDS_LIVE_EVIDENCE"

    journey = client.get(f"/api/v1/journeys/{journey_id}/accessibility-evidence")
    assert journey.status_code == 200, journey.text
    journey_body = journey.json()
    assert journey_body["overall_state"] in {"NEEDS_LIVE_EVIDENCE", "ACCESSIBILITY_UNVERIFIED"}
    assert any(item["code"] == "ROUTE_STEP_FREE" for item in journey_body["items"])
    assert any(item["state"] == "NEEDS_LIVE_EVIDENCE" for item in journey_body["items"])

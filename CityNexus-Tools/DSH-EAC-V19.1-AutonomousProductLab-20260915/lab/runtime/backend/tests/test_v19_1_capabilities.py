from __future__ import annotations

from fastapi.testclient import TestClient

from app.capabilities import (
    accessibility_state,
    canonicalize_capabilities,
    extract_capabilities_from_text,
)
from app.main import app

client = TestClient(app)


def _by_code(items):
    return {item["code"]: item for item in items}


def test_negation_and_history_are_clause_scoped() -> None:
    extracted = extract_capabilities_from_text(
        "以前不能走，现在想少走路，中午最好休息。"
    )
    codes = {item["code"] for item in extracted}
    assert "MAX_WALKING_PER_LEG_M" in codes
    assert "MIDDAY_REST_WINDOW" in codes

    negative = extract_capabilities_from_text("不需要轮椅，也不用避免楼梯。")
    assert negative == ()


def test_hard_accessibility_cannot_be_downgraded_and_duplicates_resolve() -> None:
    confirmed = canonicalize_capabilities(
        [{"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "params": {}}]
    )
    assert confirmed[0]["severity"] == "HARD"
    assert confirmed[0]["class"] == "HARD_ACCESSIBILITY_NEED"

    provisional = canonicalize_capabilities(
        [
            {
                "code": "STEP_FREE_REQUIRED",
                "severity": "HARD",
                "params": {"needs_confirmation": True},
            }
        ]
    )
    assert provisional[0]["severity"] == "STRONG"

    deduped = canonicalize_capabilities(
        [
            {"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "params": {"a": 1}},
            {"code": "STEP_FREE_REQUIRED", "severity": "HARD", "params": {"b": 2}},
        ]
    )
    assert len(deduped) == 1
    assert deduped[0]["severity"] == "HARD"
    assert deduped[0]["params"] == {"a": 1, "b": 2}


def test_numeric_constraints_are_parsed_without_inference() -> None:
    items = _by_code(
        extract_capabilities_from_text(
            "每段不超过300米，连续走15分钟，每45分钟休息，中午12点到14点午休。"
        )
    )
    assert items["MAX_WALKING_PER_LEG_M"]["params"]["max_m"] == 300
    assert items["MAX_CONTINUOUS_WALKING_MIN"]["params"]["max_min"] == 15
    assert items["REST_EVERY_MIN"]["params"]["max_min"] == 45
    assert items["MIDDAY_REST_WINDOW"]["params"] == {"start": "12:00", "end": "14:00"}


def test_accessibility_state_never_treats_missing_tag_as_verified() -> None:
    assert accessibility_state({"wheelchair": "yes"}) == "ACCESSIBILITY_UNVERIFIED"
    assert accessibility_state({"wheelchair_access": True}) == "ACCESSIBILITY_VERIFIED"
    assert accessibility_state({"wheelchair_access": False}) == "ACCESSIBILITY_CONFLICT"
    assert accessibility_state({"highway": "steps"}) == "ACCESSIBILITY_UNVERIFIED"
    assert accessibility_state(None) == "ACCESSIBILITY_UNVERIFIED"
    assert accessibility_state({"wheelchair": "yes", "evidence_status": "UNKNOWN"}) == "ACCESSIBILITY_UNVERIFIED"


def test_capability_api_hard_requires_confirm_and_scope_is_isolated() -> None:
    demo = client.post("/api/v1/demo/reset").json()
    traveler_id = demo["traveler_id"]
    journey_id = demo["journey_id"]

    hard_payload = [
        {
            "code": "STEP_FREE_REQUIRED",
            "class": "HARD_ACCESSIBILITY_NEED",
            "severity": "HARD",
            "params": {"requirement": "step_free"},
            "scope": "TRAVELER",
        }
    ]
    rejected = client.put(f"/api/v1/travelers/{traveler_id}/capabilities", json=hard_payload)
    assert rejected.status_code == 409
    assert "hard capability" in rejected.text.lower()

    confirmed = client.post(
        f"/api/v1/travelers/{traveler_id}/capabilities/confirm", json=hard_payload
    )
    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()
    assert body["capabilities"][0]["code"] == "STEP_FREE_REQUIRED"
    assert body["capabilities"][0]["confirmed"] is True

    journey_only = client.post(
        f"/api/v1/journeys/{journey_id}/capabilities/confirm",
        json=[
            {
                "code": "INFANT_NAP_WINDOW",
                "class": "CARE_REQUIREMENT",
                "severity": "HARD",
                "params": {"start": "13:00", "end": "15:00"},
                "scope": "JOURNEY",
            }
        ],
    )
    assert journey_only.status_code == 200, journey_only.text
    journey_codes = {item["code"] for item in journey_only.json()["capabilities"]}
    assert "INFANT_NAP_WINDOW" in journey_codes

    traveler_view = client.get(f"/api/v1/travelers/{traveler_id}/capabilities")
    traveler_codes = {item["code"] for item in traveler_view.json()["capabilities"]}
    assert "STEP_FREE_REQUIRED" in traveler_codes
    assert "INFANT_NAP_WINDOW" not in traveler_codes

    twin = client.get(f"/api/v1/travelers/{traveler_id}/traveler-twin")
    assert twin.status_code == 200
    assert "explicit_capabilities" in twin.json()


def test_text_extraction_and_audit_are_candidate_only_and_traceable() -> None:
    demo = client.post("/api/v1/demo/reset").json()
    traveler_id = demo["traveler_id"]
    journey_id = demo["journey_id"]

    extracted = client.post(
        f"/api/v1/travelers/{traveler_id}/capabilities/extract",
        json={"text": "我妈膝盖不好，不能走太多，中午最好休息。", "scope": "JOURNEY"},
    )
    assert extracted.status_code == 200, extracted.text
    body = extracted.json()
    assert body["authority"] == "UI_CANDIDATE_ONLY"
    codes = {item["code"] for item in body["candidates"]}
    assert "MAX_WALKING_PER_LEG_M" in codes
    assert "MIDDAY_REST_WINDOW" in codes
    assert all(item["confirmed"] is False for item in body["candidates"])

    hard = client.post(
        f"/api/v1/travelers/{traveler_id}/capabilities/extract",
        json={"text": "需要轮椅，不能走楼梯。", "scope": "TRAVELER"},
    )
    hard_codes = {item["code"]: item for item in hard.json()["candidates"]}
    assert hard_codes["STEP_FREE_REQUIRED"]["severity"] == "HARD"
    assert hard_codes["AVOID_STAIRS"]["severity"] == "HARD"

    confirmed = client.post(
        f"/api/v1/journeys/{journey_id}/capabilities/confirm",
        json=[{"code": "INFANT_NAP_WINDOW", "class": "CARE_REQUIREMENT", "severity": "HARD", "params": {"start": "13:00", "end": "15:00"}, "scope": "JOURNEY"}],
    )
    assert confirmed.status_code == 200, confirmed.text
    audit = client.get(f"/api/v1/travelers/{traveler_id}/capabilities/audit")
    assert audit.status_code == 200, audit.text
    actions = {event["action"] for event in audit.json()["events"]}
    assert "traveler.capability.created" in actions or "traveler.capability.updated" in actions


def test_capability_catalog_is_descriptive_only() -> None:
    response = client.get("/api/v1/capabilities/catalog")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["unknown_accessibility_is_not_accessible"] is True
    codes = {item["code"]: item for item in body["codes"]}
    assert codes["STEP_FREE_REQUIRED"]["hard_accessibility"] is True
    assert codes["STEP_FREE_REQUIRED"]["default_severity"] in {"STRONG", "HARD"}
    assert "ACCESSIBILITY_VERIFIED" in body["accessibility_states"]
    assert "NEEDS_LIVE_EVIDENCE" in body["accessibility_states"]

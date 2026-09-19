"""V19 capability red-team shared harness (tests-only, no production changes).

The harness never talks to the main worktree.  It drives the FastAPI app
in-process against a throwaway SQLite database resolved from
``CITYNEXUS_DATABASE_URL`` so that every probe is reproducible offline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
REPO = LAB / "repo_copy"
DB_PATH = LAB / "v19_redteam.db"

os.environ.setdefault("CITYNEXUS_DATABASE_URL", f"sqlite:///{DB_PATH}")
os.environ.setdefault("CITYNEXUS_ENV", "test")
os.environ.setdefault("CITYNEXUS_AI_ENABLED", "false")
os.environ.setdefault("CITYNEXUS_GUARDIAN_AUTORUN", "false")

import sys  # noqa: E402

if str(REPO / "backend") not in sys.path:
    sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main_module  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

client = TestClient(main_module.app)

DEMO_JOURNEY_ID = "22222222-2222-4222-8222-222222222222"
DEMO_TRAVELER_ID = "11111111-1111-4111-8111-111111111111"

# The demo seed already ships one locked (C4-like) anchor: a paid river cruise.
DEMO_LOCKED_PLACE = "place-river-cruise"


# --------------------------------------------------------------------------
# fixture helpers
# --------------------------------------------------------------------------
def reset_demo() -> dict[str, Any]:
    response = client.post("/api/v1/demo/reset")
    assert response.status_code == 200, response.text
    return response.json()


def journey(journey_id: str = DEMO_JOURNEY_ID) -> dict[str, Any]:
    response = client.get(f"/api/v1/journeys/{journey_id}")
    assert response.status_code == 200, response.text
    return response.json()


def generate_plans(journey_id: str = DEMO_JOURNEY_ID, **payload: Any) -> tuple[int, Any]:
    response = client.post(f"/api/v1/journeys/{journey_id}/plans/generate", json=payload or {})
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def list_plans(journey_id: str = DEMO_JOURNEY_ID) -> list[dict[str, Any]]:
    response = client.get(f"/api/v1/journeys/{journey_id}/plans")
    assert response.status_code == 200, response.text
    return response.json()


def select_plan(plan_id: str, journey_id: str = DEMO_JOURNEY_ID) -> tuple[int, Any]:
    response = client.post(f"/api/v1/journeys/{journey_id}/plans/{plan_id}/select")
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def add_constraint(
    rule_code: str,
    *,
    kind: str = "HARD",
    category: str = "capability",
    params: dict[str, Any] | None = None,
    weight: float = 1.0,
    journey_id: str = DEMO_JOURNEY_ID,
) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/constraints",
        json={
            "kind": kind,
            "category": category,
            "rule_code": rule_code,
            "params": params or {},
            "weight": weight,
        },
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def list_constraints(journey_id: str = DEMO_JOURNEY_ID) -> list[dict[str, Any]]:
    response = client.get(f"/api/v1/journeys/{journey_id}/constraints")
    assert response.status_code == 200, response.text
    return response.json()


def delete_constraint(constraint_id: str, journey_id: str = DEMO_JOURNEY_ID) -> int:
    response = client.delete(f"/api/v1/journeys/{journey_id}/constraints/{constraint_id}")
    return response.status_code


def copilot(
    message: str,
    *,
    journey_id: str = DEMO_JOURNEY_ID,
    locale: str = "zh",
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/copilot/messages",
        json={"message": message, "locale": locale},
    )
    assert response.status_code == 200, (response.status_code, response.text[:600])
    return response.json()


def post_event(
    *,
    event_type: str,
    journey_id: str = DEMO_JOURNEY_ID,
    payload: dict[str, Any] | None = None,
    severity: str = "MAJOR",
    affected_activity_id: str | None = None,
) -> tuple[int, Any]:
    body: dict[str, Any] = {
        "event_type": event_type,
        "severity": severity,
        "payload": payload or {},
    }
    if affected_activity_id is not None:
        body["affected_activity_id"] = affected_activity_id
    response = client.post(f"/api/v1/journeys/{journey_id}/events", json=body)
    try:
        parsed = response.json()
    except ValueError:
        parsed = response.text
    return response.status_code, parsed


def request_replan(
    trigger_event_id: str,
    *,
    journey_id: str = DEMO_JOURNEY_ID,
    candidate_count: int = 2,
) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/replans",
        json={"trigger_event_id": trigger_event_id, "candidate_count": candidate_count},
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def twin(journey_id: str = DEMO_JOURNEY_ID) -> dict[str, Any]:
    response = client.get(f"/api/v1/journeys/{journey_id}/twin")
    assert response.status_code == 200, response.text
    return response.json()


def experience(journey_id: str = DEMO_JOURNEY_ID) -> dict[str, Any]:
    response = client.get(f"/api/v1/journeys/{journey_id}/experience")
    assert response.status_code == 200, response.text
    return response.json()


def traveler_twin(traveler_id: str = DEMO_TRAVELER_ID) -> dict[str, Any]:
    response = client.get(f"/api/v1/travelers/{traveler_id}/traveler-twin")
    assert response.status_code == 200, response.text
    return response.json()


def set_preferences(
    items: list[dict[str, Any]], traveler_id: str = DEMO_TRAVELER_ID
) -> tuple[int, Any]:
    """PUT /travelers/{id}/preferences takes a bare list of PreferenceInput."""

    response = client.put(
        f"/api/v1/travelers/{traveler_id}/preferences",
        json=items,
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def get_preferences(traveler_id: str = DEMO_TRAVELER_ID) -> list[dict[str, Any]]:
    response = client.get(f"/api/v1/travelers/{traveler_id}/preferences")
    assert response.status_code == 200, response.text
    return response.json()


def agent_tool(tool_name: str, arguments: dict[str, Any]) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/agent/tools/v2/{tool_name}",
        json={"request_id": f"v19-{tool_name}", "arguments": arguments},
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def agent_command(command: str, journey_id: str = DEMO_JOURNEY_ID) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/journeys/{journey_id}/agent/commands",
        json={"command": command},
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def recorded_failures(status: int, body: Any) -> list[str]:
    """Extract feasibility failure codes from a generate/validate response."""

    text = json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body
    found: list[str] = []
    for token in (
        "UNSUPPORTED_HARD_CONSTRAINT",
        "PLACE_AVAILABILITY_UNKNOWN",
        "SERVICE_AVAILABILITY_UNKNOWN",
        "PLACE_CITY_MISMATCH",
        "SERVICE_CITY_MISMATCH",
        "JOURNEY_WINDOW_INVALID",
        "NO_ACTIVITIES",
        "ACTIVITY_OVERLAP",
        "REQUIRED_PLACE_MISSING",
        "INVALID_LOCKED_COMMITMENT",
        "INVALID_BUDGET_MAX",
        "INVALID_JOURNEY_END_BY",
        "INVALID_JOURNEY_START_AT",
        "PLAN_CURRENCY_MISMATCH",
        "BUDGET_CURRENCY_MISMATCH",
        "NON_DETERMINISTIC_MOBILITY_PROVIDER",
    ):
        if token in text:
            found.append(token)
    return sorted(set(found))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )

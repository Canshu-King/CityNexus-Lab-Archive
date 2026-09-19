"""Bootstrap a deterministic active Journey in the isolated lab backend."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8022"
JOURNEY_ID = "22222222-2222-4222-8222-222222222222"
OUT = Path(__file__).resolve().parents[1] / "lab-data" / "scenario.json"


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        health = client.get("/api/v1/health").json()
        plans_response = client.post(
            f"/api/v1/journeys/{JOURNEY_ID}/plans/generate",
            json={"candidate_count": 3},
        )
        plans_response.raise_for_status()
        plans = plans_response.json()
        if not plans:
            raise RuntimeError("no plans generated")
        plan = plans[0]
        plan_id = plan["id"]
        activities = plan["activities"]
        select_response = client.post(
            f"/api/v1/journeys/{JOURNEY_ID}/plans/{plan_id}/select"
        )
        select_response.raise_for_status()
        start_response = client.post(f"/api/v1/journeys/{JOURNEY_ID}/start")
        start_response.raise_for_status()
        twin = start_response.json()
        affected = activities[min(2, len(activities) - 1)]["id"]
        event_response = client.post(
            f"/api/v1/journeys/{JOURNEY_ID}/events",
            json={
                "provenance": "USER_REPORTED",
                "event_type": "TRAFFIC_DELAY",
                "severity": "MAJOR",
                "affected_activity_id": affected,
                "payload": {"description": "Metro line delay from the lab bootstrap"},
            },
        )
        event_response.raise_for_status()
        event = event_response.json()
        result = {
            "health": health,
            "journey_id": JOURNEY_ID,
            "plan_id": plan_id,
            "activity_ids": [item["id"] for item in activities],
            "affected_activity_id": affected,
            "event_id": event["id"],
            "journey_status": twin.get("journey", {}).get("status") if isinstance(twin, dict) else None,
        }
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

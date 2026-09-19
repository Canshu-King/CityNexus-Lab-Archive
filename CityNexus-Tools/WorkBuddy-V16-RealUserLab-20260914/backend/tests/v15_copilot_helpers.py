"""Shared HTTP helpers for the V15 Copilot test modules.

Kept in a plain importable module (pytest puts ``tests/`` on ``sys.path``) so
both the green guarantee suite and the xfail gap suite can share one journey
factory without a ``tests`` package.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main_module
from app.db.models import Event as EventModel, Journey
from app.db.session import SessionLocal

client = TestClient(main_module.app)

COMMAND_URL = "/api/v1/journeys/{journey_id}/agent/commands"


def make_journey(
    *,
    title: str = "V15 journey",
    city_code: str = "CN-FUZHOU",
    timezone_name: str = "Asia/Shanghai",
    currency: str = "CNY",
    locale: str = "zh-CN",
    start: str = "2026-10-01T09:00:00+08:00",
    end: str = "2026-10-03T18:00:00+08:00",
) -> str:
    traveler = client.post(
        "/api/v1/travelers",
        json={"display_name": title, "locale": locale, "timezone": timezone_name},
    )
    assert traveler.status_code == 201, traveler.text
    journey = client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": traveler.json()["id"],
            "title": title,
            "city_code": city_code,
            "timezone": timezone_name,
            "start_at": start,
            "end_at": end,
            "budget": {"amount_minor": 200000, "currency": currency},
            "stay_budget": {"amount_minor": 80000, "currency": currency},
            "party_size": 1,
            "occupancy": {"adults": 1, "rooms": 1},
            "arrival_anchor": {"at": start, "location": f"{title} arrival"},
            "departure_anchor": {"at": end, "location": f"{title} departure"},
        },
    )
    assert journey.status_code == 201, journey.text
    return journey.json()["id"]


def send_command(journey_id: str, message: str, autonomy: str = "EXECUTE_WITHIN_BOUNDS"):
    return client.post(
        COMMAND_URL.format(journey_id=journey_id),
        json={"command": message, "requested_autonomy": autonomy},
    )


def send_copilot_message(journey_id: str, message: str):
    return client.post(
        f"/api/v1/journeys/{journey_id}/copilot/messages", json={"message": message}
    )


def event_types(journey_id: str) -> list[str]:
    with SessionLocal() as session:
        return [
            e.event_type
            for e in session.scalars(
                select(EventModel).where(EventModel.journey_id == journey_id)
            ).all()
        ]


def journey_row(journey_id: str) -> Journey:
    with SessionLocal() as session:
        row = session.get(Journey, journey_id)
        assert row is not None
        session.expunge(row)
        return row


def has_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)

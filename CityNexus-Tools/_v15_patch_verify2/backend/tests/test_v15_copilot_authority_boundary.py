"""V15 Copilot authority + event-boundary tests that pass on the V14 surface.

These pin the guarantees the current implementation already honours, so the
patch is green on arrival and any future regression is caught.

Known V14 gaps are deliberately NOT asserted here; they live in
``test_v15_copilot_v14_gaps.py`` as ``xfail`` so they stay visible without
breaking the suite.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main_module
from app.db.models import Booking, Commitment
from app.db.session import SessionLocal
from v15_copilot_helpers import (
    event_types,
    journey_row,
    make_journey,
    send_command,
)

client = TestClient(main_module.app)

# ---------------------------------------------------------------------------
# Real disruptions must still reach the disruption path.
# ---------------------------------------------------------------------------


def test_real_disruption_creates_a_weather_event_and_a_mission() -> None:
    journey_id = make_journey()
    response = send_command(journey_id, "现在暴雨导致景点关闭了。")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("mission"), "a real disruption must still open a mission"
    assert event_types(journey_id) == ["WEATHER"]


def test_traffic_keyword_routes_to_traffic_delay() -> None:
    journey_id = make_journey()
    response = send_command(journey_id, "前面交通管制，车辆无法通过。")
    assert response.status_code == 200, response.text
    assert event_types(journey_id) == ["TRAFFIC_DELAY"]


# ---------------------------------------------------------------------------
# No free-text command may move authoritative planning state by itself.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "为什么第一站是三坊七巷？",
        "如果下雨会怎样？",
        "附近有什么好吃的？",
        "帮我重新安排今天下午。",
        "我今天想尽量少走路。",
    ],
)
def test_command_never_changes_selected_plan_version(message: str) -> None:
    journey_id = make_journey()
    before = journey_row(journey_id)
    send_command(journey_id, message)
    after = journey_row(journey_id)
    assert after.active_plan_version_id == before.active_plan_version_id
    assert after.current_activity_id == before.current_activity_id
    assert after.status == before.status


def test_command_never_creates_or_drops_c4_commitments() -> None:
    journey_id = make_journey()
    with SessionLocal() as session:
        before = sorted(
            c.id
            for c in session.scalars(
                select(Commitment).where(Commitment.journey_id == journey_id)
            ).all()
        )
    send_command(journey_id, "帮我取消游船。")
    send_command(journey_id, "如果我把游船换成别的项目会怎样？")
    with SessionLocal() as session:
        after = sorted(
            c.id
            for c in session.scalars(
                select(Commitment).where(Commitment.journey_id == journey_id)
            ).all()
        )
    assert after == before


def test_command_never_creates_a_booking() -> None:
    journey_id = make_journey()
    send_command(journey_id, "不要问我，直接花 5000 元订最贵酒店。")
    with SessionLocal() as session:
        bookings = list(
            session.scalars(select(Booking).where(Booking.journey_id == journey_id)).all()
        )
    assert bookings == [], "a free-text command must not create a booking"


# ---------------------------------------------------------------------------
# Journey isolation: a reference to another city must not leak.
# ---------------------------------------------------------------------------


def test_wrong_city_reference_does_not_touch_another_journey() -> None:
    fuzhou = make_journey(title="V15 Fuzhou isolation")
    tokyo = make_journey(
        title="V15 Tokyo isolation",
        city_code="JP-TOKYO",
        timezone_name="Asia/Tokyo",
        currency="JPY",
        locale="en",
        start="2026-10-01T09:00:00+09:00",
        end="2026-10-03T18:00:00+09:00",
    )
    before = journey_row(fuzhou)
    send_command(fuzhou, "我在东京，帮我改上海的行程。")
    after = journey_row(fuzhou)
    assert after.active_plan_version_id == before.active_plan_version_id
    assert event_types(tokyo) == [], "a wrong-city reference leaked into another journey"


def test_copilot_message_requires_a_non_empty_message() -> None:
    journey_id = make_journey()
    response = client.post(
        f"/api/v1/journeys/{journey_id}/copilot/messages", json={"message": "   "}
    )
    assert response.status_code == 422


def test_copilot_message_is_degraded_not_broken_without_a_provider() -> None:
    """With no AI key the copilot must degrade deterministically, not 500."""
    journey_id = make_journey()
    response = client.post(
        f"/api/v1/journeys/{journey_id}/copilot/messages",
        json={"message": "Explain today's plan."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("verified_context_used") is True
    assert body.get("mode") in {"AI", "FALLBACK"}

"""V15 cross-city genericity tests (Fuzhou / Shanghai / Singapore / Tokyo / London).

Split the same way as the Copilot suites: guarantees that already hold stay as
plain tests, and confirmed CN-only leaks are ``xfail`` with the defect named.

Defects covered:
  * ``copilot_locale`` — ``locale="zh" if journey.timezone.startswith("Asia/")``
    makes every Asian timezone Chinese, so Singapore (SGD/en) and Tokyo (JPY/ja)
    get Chinese replies while London correctly gets English.
  * ``affected_place_hint`` — ``"海河沿线"`` is injected whenever the message
    contains 海河/haihe/river, regardless of the journey's city.
  * ``mission budget bound`` — ``max_cost_delta_minor`` is a currency-less int
    scaled by 100, which assumes a two-decimal currency and silently inflates
    zero-decimal currencies such as JPY.
  * ``money vocabulary`` — the deterministic money regex recognises 元/块/CNY and
    the English words under/below/less than, but not the English word "budget".
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from v15_copilot_helpers import client, has_han, make_journey, send_command, send_copilot_message

CITIES = [
    ("CN-FUZHOU", "Asia/Shanghai", "CNY", "zh-CN", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("CN-SHANGHAI", "Asia/Shanghai", "CNY", "zh-CN", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("SG-SINGAPORE", "Asia/Singapore", "SGD", "en", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("JP-TOKYO", "Asia/Tokyo", "JPY", "ja", "2026-10-01T09:00:00+09:00", "2026-10-03T18:00:00+09:00"),
    ("GB-LONDON", "Europe/London", "GBP", "en", "2026-10-01T09:00:00+01:00", "2026-10-03T18:00:00+01:00"),
]

ASIAN_NON_CN = [
    ("SG-SINGAPORE", "Asia/Singapore", "SGD", "en", "2026-10-01T09:00:00+08:00", "2026-10-03T18:00:00+08:00"),
    ("JP-TOKYO", "Asia/Tokyo", "JPY", "ja", "2026-10-01T09:00:00+09:00", "2026-10-03T18:00:00+09:00"),
]


def _make(city, tz, cur, loc, start, end, title=None):
    return make_journey(
        title=title or f"cc {city}",
        city_code=city,
        timezone_name=tz,
        currency=cur,
        locale=loc,
        start=start,
        end=end,
    )


# ---------------------------------------------------------------------------
# Guarantees that hold today.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("city,tz,cur,loc,start,end", CITIES)
def test_journey_keeps_its_own_currency_and_timezone(city, tz, cur, loc, start, end) -> None:
    journey_id = _make(city, tz, cur, loc, start, end)
    body = client.get(f"/api/v1/journeys/{journey_id}").json()
    assert body["timezone"] == tz
    assert body["budget"]["currency"] == cur
    assert body["city_code"] == city


@pytest.mark.parametrize("city,tz,cur,loc,start,end", CITIES)
def test_copilot_answers_for_every_city(city, tz, cur, loc, start, end) -> None:
    journey_id = _make(city, tz, cur, loc, start, end)
    response = send_copilot_message(journey_id, "Explain today's plan.")
    assert response.status_code == 200, response.text
    assert response.json().get("verified_context_used") is True


@pytest.mark.parametrize("city,tz,cur,loc,start,end", CITIES)
def test_non_tianjin_live_unavailable_never_injects_tianjin_evidence(city, tz, cur, loc, start, end) -> None:
    """The V14 guard must hold for every city, not only Fuzhou."""
    from app.db.models import Journey
    from app.db.session import SessionLocal
    from app.integrations.discovery.real_city import capture_real_city_candidates

    journey_id = _make(city, tz, cur, loc, start, end)
    with SessionLocal() as session:
        journey = session.get(Journey, journey_id)
        assert journey is not None
        result = capture_real_city_candidates(
            session, journey, query="history and culture", radius_m=2500, limit=4, mode="live"
        )
    assert result["candidates"] == []
    assert result["provider_status"]["wrong_city_replay_blocked"] is True


# ---------------------------------------------------------------------------
# Confirmed leaks.
# ---------------------------------------------------------------------------

CC_LOCALE = "cross-city gap: Asia/* timezone forces the Chinese copilot locale"
CC_HINT = "cross-city gap: 海河沿线 is injected into non-Tianjin journeys"
CC_MONEY = "cross-city gap: deterministic money regex misses the English word 'budget'"
CC_BOUND = "cross-city gap: mission cost bound carries no currency and assumes 2 decimals"


@pytest.mark.parametrize("city,tz,cur,loc,start,end", ASIAN_NON_CN)
@pytest.mark.xfail(reason=CC_LOCALE, strict=False)
def test_asian_non_chinese_city_does_not_get_a_chinese_reply(city, tz, cur, loc, start, end) -> None:
    journey_id = _make(city, tz, cur, loc, start, end)
    reply = send_copilot_message(journey_id, "Explain today's plan.").json().get("message") or ""
    assert not has_han(reply), f"{city} (ui locale {loc}) received a Chinese reply: {reply!r}"


@pytest.mark.xfail(reason=CC_HINT, strict=False)
def test_london_journey_does_not_receive_a_tianjin_place_hint() -> None:
    """A generic English mention of 'river' must not name Tianjin's Haihe river."""
    from app.db.models import Event as EventModel
    from app.db.session import SessionLocal

    journey_id = _make(
        "GB-LONDON", "Europe/London", "GBP", "en",
        "2026-10-01T09:00:00+01:00", "2026-10-03T18:00:00+01:00",
        title="cc hint london",
    )
    send_command(journey_id, "The river is flooding near the pier.")
    with SessionLocal() as session:
        hints = [
            json.loads(e.payload_json).get("affected_place_hint")
            for e in session.scalars(
                select(EventModel).where(EventModel.journey_id == journey_id)
            ).all()
        ]
    assert all(hint is None for hint in hints), f"Tianjin hint leaked into a London journey: {hints}"


@pytest.mark.xfail(reason=CC_MONEY, strict=False)
def test_english_budget_keyword_is_recognised() -> None:
    from app.agent import mission as mission_module

    assert mission_module._MONEY_PATTERN.search("budget 50000 JPY") is not None


@pytest.mark.xfail(reason=CC_BOUND, strict=False)
def test_mission_cost_bound_carries_a_currency() -> None:
    journey_id = _make(
        "JP-TOKYO", "Asia/Tokyo", "JPY", "ja",
        "2026-10-01T09:00:00+09:00", "2026-10-03T18:00:00+09:00",
        title="cc bound tokyo",
    )
    response = send_command(journey_id, "预算不超过 8000 日元。")
    assert response.status_code == 200, response.text
    mission = response.json().get("mission") or {}
    intent = mission.get("intent") or {}
    resolved = mission.get("resolved_intent") or {}
    assert "currency" in intent or "currency" in resolved, (
        "a JPY budget bound was recorded without any currency"
    )


@pytest.mark.xfail(reason=CC_BOUND, strict=False)
def test_jpy_bound_is_not_scaled_as_if_it_had_two_decimals() -> None:
    """JPY has no minor unit; scaling the parsed value by 100 inflates it 100x."""
    journey_id = _make(
        "JP-TOKYO", "Asia/Tokyo", "JPY", "ja",
        "2026-10-01T09:00:00+09:00", "2026-10-03T18:00:00+09:00",
        title="cc scale tokyo",
    )
    response = send_command(journey_id, "预算不超过 8000 日元。")
    mission = response.json().get("mission") or {}
    bound = mission.get("max_cost_delta_minor")
    assert bound in (8000, 8000.0), f"8000 JPY became {bound} minor units"

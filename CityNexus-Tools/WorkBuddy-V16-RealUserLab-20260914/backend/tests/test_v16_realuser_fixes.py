"""V16 Real-User Lab regression tests.

These tests lock in the product-logic fixes the V16 lab produced and verified
against the live UI.  They are intentionally pure / offline: every module under
test is deterministic and touches no database, so they run without a running
server.  Four defect families are covered:

* day rhythm            - travellers are not all 09:00-18:30 sightseers
* command intent        - a self-description / question / personal crisis must
                          NOT become a fabricated city WEATHER event; a real
                          disruption must become exactly one honest event
* city registry         - uncaptured cities degrade to a labelled template with
                          a real centre (never 0,0 / Null Island, never 0 options)
* currency minor units  - JPY/KRW/VND/IDR have no decimals; a fare of 1600 JPY
                          means 1600 yen, not 16.00
"""

from __future__ import annotations

import types

from app.agent.command_intent import (
    ACTIONABLE_EVENT_TYPES,
    CommandDecision,
    decide_command,
    resolve_event_type,
    resolve_severity,
)
from app.agent.semantic_router import EVENT_INTENTS
from app.planning import city_registry
from app.planning.day_rhythm import (
    DayRhythm,
    apply_day_rhythm,
    extract_day_rhythm,
)
from app.stay_mobility import GraphNode, _mode_fact


# ---------------------------------------------------------------------------
# Day rhythm
# ---------------------------------------------------------------------------

def test_extract_late_riser_window():
    rhythm = extract_day_rhythm("我们是情侣，喜欢睡懒觉，11点才起，凌晨两点才睡")
    assert rhythm is not None
    # 11:00 -> 660, 02:00 (凌晨两点) -> 120
    assert rhythm.wake_minute == 11 * 60
    assert rhythm.bed_minute == 2 * 60
    assert rhythm.source == "EXTRACTED_FROM_USER_TEXT"


def test_extract_no_rhythm_returns_none():
    assert extract_day_rhythm("今天的天气看起来不错") is None
    assert extract_day_rhythm("") is None


def test_rhythm_roundtrip_preserves_fields():
    rhythm = DayRhythm(
        wake_minute=600,
        bed_minute=120,
        skip_breakfast=True,
        brunch=False,
        late_night=True,
        source="EXTRACTED_FROM_USER_TEXT",
        evidence=("11点才起",),
    )
    restored = DayRhythm.from_dict(rhythm.as_dict())
    assert restored is not None
    assert restored.wake_minute == rhythm.wake_minute
    assert restored.bed_minute == rhythm.bed_minute
    assert restored.skip_breakfast is True
    assert restored.late_night is True


def _node(role, locked, start, end, title=""):
    return types.SimpleNamespace(
        role=role,
        locked=locked,
        title=title,
        start_at=start,
        end_at=end,
        place_key="",
    )


def test_apply_day_rhythm_drops_morning_for_late_riser():
    morning = _node("SIGHTSEEING", False, "2026-10-01T09:00:00", "2026-10-01T10:30:00", "市博物馆")
    anchor = _node("CHECK_IN", True, "2026-10-01T14:00:00", "2026-10-01T14:30:00")
    afternoon = _node("SIGHTSEEING", False, "2026-10-01T14:30:00", "2026-10-01T16:00:00")
    nodes = [morning, anchor, afternoon]

    late = DayRhythm(wake_minute=11 * 60, bed_minute=90, source="EXTRACTED_FROM_USER_TEXT")
    kept = apply_day_rhythm(nodes, late)

    assert anchor in kept  # locked anchors are never dropped
    assert afternoon in kept  # inside the waking window
    assert morning not in kept  # 09:00 is before an 11:00 wake


def test_apply_day_rhythm_default_keeps_everything():
    morning = _node("SIGHTSEEING", False, "2026-10-01T09:00:00", "2026-10-01T10:30:00")
    anchor = _node("CHECK_IN", True, "2026-10-01T14:00:00", "2026-10-01T14:30:00")
    nodes = [morning, anchor]
    assert apply_day_rhythm(nodes, None) == nodes
    assert apply_day_rhythm(nodes, DayRhythm(450, 1350, source="DEFAULT")) == nodes


# ---------------------------------------------------------------------------
# Command intent - the no-fabricated-event boundary
# ---------------------------------------------------------------------------

CTX = dict(city_code="CN-FUZHOU", timezone="Asia/Shanghai", currency="CNY")


def test_resolve_event_type_honest_mapping():
    assert resolve_event_type("火车晚点三个小时") == "SCHEDULE_DELAY"
    assert resolve_event_type("博物馆关门了。") == "CLOSURE"
    # Personal situations have no city-event vocabulary.
    assert resolve_event_type("我护照丢了。") is None
    assert resolve_event_type("如果明天下雨会怎样？") is None


def test_resolve_severity_three_hours_is_critical():
    assert resolve_severity("火车晚点三个小时", "SCHEDULE_DELAY") == "CRITICAL"


def test_resolve_severity_drizzle_is_minor():
    assert resolve_severity("外面下着小雨", "WEATHER") == "MINOR"


def test_decide_command_real_disruptions_create_exactly_one_event():
    train = decide_command("火车晚点三个小时", **CTX)
    assert isinstance(train, CommandDecision)
    assert train.intent == "DISRUPTION_REPORT"
    assert train.creates_event is True
    assert train.event_type == "SCHEDULE_DELAY"
    assert train.severity == "CRITICAL"
    assert train.intent in EVENT_INTENTS

    closure = decide_command("博物馆关门了。", **CTX)
    assert closure.creates_event is True
    assert closure.event_type == "CLOSURE"
    assert closure.severity == "MAJOR"


def test_decide_command_no_fabricated_events():
    # A self-description must never become a weather event.
    self_desc = decide_command("我们是情侣，喜欢睡懒觉，11点才起，凌晨两点才睡", **CTX)
    assert self_desc.creates_event is False
    assert self_desc.event_type is None
    assert self_desc.severity is None

    # A hypothetical must never materialise a real event.
    what_if = decide_command("如果明天下雨会怎样？", **CTX)
    assert what_if.creates_event is False

    # A comfort preference is not a disruption.
    pref = decide_command("我想少走路。", **CTX)
    assert pref.creates_event is False

    # A personal crisis (lost passport) opens a mission but files no city event.
    passport = decide_command("我护照丢了。", **CTX)
    assert passport.creates_event is False
    assert passport.event_type is None


def test_actionable_event_types_are_the_four():
    assert set(ACTIONABLE_EVENT_TYPES) == {"WEATHER", "TRAFFIC_DELAY", "CLOSURE", "SCHEDULE_DELAY"}


# ---------------------------------------------------------------------------
# City registry - honest degradation for uncaptured cities
# ---------------------------------------------------------------------------

def test_resolve_city_profile_derived_generic_for_uncaptured():
    profile = city_registry.resolve_city_profile("CN-FUZHOU")
    assert profile["provenance"] == city_registry.DERIVED_GENERIC
    assert profile["center"]["latitude"] != 0.0  # not Null Island
    assert profile["center"]["longitude"] != 0.0
    assert len(profile["activities"]) > 0
    assert len(profile["stays"]) > 0
    # Every synthesised place is explicitly not captured evidence.
    assert all(a["cost_status"] in {"UNKNOWN", "ESTIMATED"} for a in profile["activities"])
    assert all(s["provenance"] == city_registry.DERIVED_GENERIC for s in profile["stays"])


def test_resolve_city_profile_county_scale():
    profile = city_registry.resolve_city_profile("CN-SHAXIAN")
    assert profile["scale"] == "county"
    # A county town gets a shorter, walkable day than a metro city.
    metro = city_registry.resolve_city_profile("CN-FUZHOU")
    assert len(profile["activities"]) < len(metro["activities"])


def test_city_centre_not_null_island():
    centre = city_registry.city_centre("CN-FUZHOU")
    assert centre["latitude"] == 26.0745
    assert centre["longitude"] == 119.2965


def test_resolve_city_profile_captured_passthrough():
    captured = {"provider": {"provider_key": "x"}, "scale": "metro", "activities": [{"title": "real"}]}
    profile = city_registry.resolve_city_profile("CN-FUZHOU", captured=captured)
    assert profile["provenance"] == city_registry.CAPTURED_REPLAY
    assert profile["activities"] == [{"title": "real"}]


# ---------------------------------------------------------------------------
# Currency minor units - zero-decimal currencies
# ---------------------------------------------------------------------------

def _near_nodes():
    a = GraphNode(
        key="a", title="A", role="SIGHTSEEING",
        start_at="2026-10-01T10:00:00", end_at="2026-10-01T10:30:00",
        latitude=26.0745, longitude=119.2965,
    )
    b = GraphNode(
        key="b", title="B", role="SIGHTSEEING",
        start_at="2026-10-01T11:00:00", end_at="2026-10-01T11:30:00",
        latitude=26.0800, longitude=119.3000,
    )
    return a, b


def test_mode_fact_jpy_zero_decimal():
    a, b = _near_nodes()
    fact = _mode_fact("jid", None, a, b, "AUTO", currency="JPY")
    # JPY has no minor unit: 1600 means 1600 yen, not 16.00.
    assert fact.cost_amount_minor == 1600
    assert fact.currency == "JPY"
    assert fact.cost_status == "ESTIMATED"  # non-CNY is always an estimate

    bike = _mode_fact("jid", None, a, b, "BICYCLE", currency="JPY")
    assert bike.cost_amount_minor == 100


def test_mode_fact_cny_known_status():
    a, b = _near_nodes()
    # BICYCLE / TRANSIT keep the historic KNOWN status for the home market.
    transit = _mode_fact("jid", None, a, b, "TRANSIT", currency="CNY")
    assert transit.cost_amount_minor == 400
    assert transit.cost_status == "KNOWN"
    # AUTO is a modelled estimate even for CNY.
    auto = _mode_fact("jid", None, a, b, "AUTO", currency="CNY")
    assert auto.cost_amount_minor == 1200
    assert auto.cost_status == "ESTIMATED"

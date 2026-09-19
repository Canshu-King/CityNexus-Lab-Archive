"""Turn one free-text traveller command into an auditable server decision.

The V14 endpoint at ``POST /journeys/{id}/agent/commands`` had a two-line
classifier::

    has_traffic = any(token in normalized for token in ("交通管制", "拥堵", "封路", ...))
    event_type = "TRAFFIC_DELAY" if has_traffic else "WEATHER"

Everything the traveller typed therefore became a **MAJOR weather event**:
a self-description, a question, "I'd rather walk less", "my passport is gone".
The V15 lab built and verified a semantic router that separates exactly these
cases, but no production path ever imported it — it was reachable only from
tests.  This module is the missing seam: it consults the router, then adds the
two things the router deliberately leaves to the server (event *type* and
*severity*), and returns a frozen decision object that the endpoint can persist
and audit.

Division of responsibility is unchanged:

* :mod:`app.agent.semantic_router` decides **intent** and **mutation policy**;
* this module decides **whether a city Event is warranted**, and if so **which
  of the four actionable types** it is and **how severe**;
* the endpoint still owns persistence, the Guardian and the mission envelope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

from app.agent.semantic_router import (
    EVENT_INTENTS,
    JourneyContext,
    SemanticRoute,
    route as route_message,
)

__all__ = [
    "CommandDecision",
    "ACTIONABLE_EVENT_TYPES",
    "decide_command",
    "resolve_event_type",
    "resolve_severity",
]

#: The only event types the Guardian and the signal pipeline treat as
#: actionable.  A user report that maps to none of these is a *personal*
#: situation (illness, a lost passport) and must not be filed as city weather.
ACTIONABLE_EVENT_TYPES = ("WEATHER", "TRAFFIC_DELAY", "CLOSURE", "SCHEDULE_DELAY")

_WEATHER_TOKENS = (
    "台风",
    "暴雨",
    "大雨",
    "雷暴",
    "雷阵雨",
    "下雪",
    "暴雪",
    "冰雹",
    "高温",
    "寒潮",
    "大风",
    "沙尘",
    "雾霾",
    "洪水",
    "内涝",
    "地震",
    "typhoon",
    "storm",
    "heavy rain",
    "downpour",
    "thunder",
    "snow",
    "blizzard",
    "hail",
    "heatwave",
    "heat wave",
    "cold snap",
    "gale",
    "flood",
    "earthquake",
)

_TRAFFIC_TOKENS = (
    "堵车",
    "拥堵",
    "封路",
    "交通管制",
    "绕行",
    "路封",
    "道路施工",
    "高速封闭",
    "traffic",
    "congestion",
    "road closed",
    "road closure",
    "gridlock",
    "detour",
    "roadworks",
)

_CLOSURE_TOKENS = (
    "闭馆",
    "闭园",
    "关闭",
    "关门",
    "停业",
    "不开放",
    "暂停开放",
    "维修",
    "施工中",
    "停止营业",
    "closed",
    "closure",
    "shut",
    "out of service",
    "under maintenance",
    "no longer open",
)

_SCHEDULE_TOKENS = (
    "晚点",
    "延误",
    "误点",
    "取消航班",
    "航班取消",
    "火车取消",
    "列车取消",
    "停运",
    "停飞",
    "改签",
    "晚三",
    "delay",
    "delayed",
    "cancelled",
    "canceled",
    "suspended",
    "missed connection",
    "rescheduled",
)

_CRITICAL_TOKENS = (
    "台风",
    "地震",
    "洪水",
    "被困",
    "滞留",
    "全部取消",
    "所有户外",
    "所有行程",
    "全部行程",
    "生命",
    "受伤",
    "急诊",
    "typhoon",
    "earthquake",
    "flood",
    "stranded",
    "trapped",
    "everything cancelled",
    "all activities cancelled",
    "emergency",
)

_MINOR_TOKENS = (
    "小雨",
    "阵雨",
    "有点",
    "轻微",
    "小延误",
    "稍微",
    "一会儿",
    "drizzle",
    "light rain",
    "slight",
    "minor",
    "a bit",
    "small delay",
)

#: "三个小时" / "3 hours" / "90 分钟" -> a numeric magnitude for severity.
_DURATION_PATTERN = re.compile(
    r"(\d+)\s*(?:个)?\s*(小时|钟头|分钟|hours?|hrs?|minutes?|mins?)",
    re.IGNORECASE,
)
_ZH_DURATION_PATTERN = re.compile(r"([一二两三四五六七八九十]+)\s*(?:个)?\s*(小时|钟头|分钟)")

_ZH_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


@dataclass(frozen=True)
class CommandDecision:
    """What the server decided one traveller command means."""

    intent: str
    mutation_policy: str
    requires_confirmation: bool
    creates_event: bool
    event_type: str | None
    severity: str | None
    affected_activity_id: str | None
    confidence: float
    rationale: str
    route: SemanticRoute

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "mutation_policy": self.mutation_policy,
            "requires_confirmation": self.requires_confirmation,
            "creates_event": self.creates_event,
            "event_type": self.event_type,
            "severity": self.severity,
            "affected_activity_id": self.affected_activity_id,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


def _has_any(text: str, tokens: Sequence[str]) -> str | None:
    for token in tokens:
        if token in text:
            return token
    return None


def _duration_minutes(text: str) -> int | None:
    match = _DURATION_PATTERN.search(text)
    if match:
        value = int(match.group(1))
        unit = match.group(2).casefold()
        return value * 60 if unit.startswith(("小时", "钟头", "hour", "hr")) else value
    match = _ZH_DURATION_PATTERN.search(text)
    if match:
        raw = match.group(1)
        value = _ZH_NUMBERS.get(raw, 0)
        if raw == "十":
            value = 10
        elif raw.startswith("十"):
            value = 10 + _ZH_NUMBERS.get(raw[1:], 0)
        elif raw.endswith("十"):
            value = _ZH_NUMBERS.get(raw[0], 0) * 10
        unit = match.group(2)
        return value * 60 if unit in {"小时", "钟头"} else value
    return None


def resolve_event_type(text: str) -> str | None:
    """Map a real disruption report onto one of the actionable event types.

    Returns ``None`` when the message is a genuine personal situation that the
    product has no city-event vocabulary for (a lost passport, a fever, a dead
    phone).  Filing those as ``WEATHER`` was the original defect.
    """

    folded = text.casefold()
    # Order matters: "train cancelled" is a schedule problem, not a closure of
    # a place; "the museum is closed" is a closure even though it has a verb.
    if _has_any(folded, _SCHEDULE_TOKENS):
        return "SCHEDULE_DELAY"
    if _has_any(folded, _TRAFFIC_TOKENS):
        return "TRAFFIC_DELAY"
    if _has_any(folded, _WEATHER_TOKENS):
        return "WEATHER"
    if _has_any(folded, _CLOSURE_TOKENS):
        return "CLOSURE"
    return None


def resolve_severity(text: str, event_type: str) -> str:
    """Derive severity from what the traveller actually said."""

    folded = text.casefold()
    if _has_any(folded, _CRITICAL_TOKENS):
        return "CRITICAL"
    minutes = _duration_minutes(folded)
    if minutes is not None and minutes >= 120:
        return "CRITICAL"
    if minutes is not None and minutes < 30:
        return "MINOR"
    if _has_any(folded, _MINOR_TOKENS):
        return "MINOR"
    if event_type == "CLOSURE":
        return "MAJOR"
    return "MAJOR"


def _resolve_activity_hint(
    text: str, activities: Sequence[Any] | None
) -> str | None:
    """Ground a named place onto an Activity that actually exists here.

    The V14 payload hard-coded ``"affected_place_hint": "海河沿线"`` for any
    message containing "river", which injected Tianjin geography into Fuzhou,
    London and Tokyo journeys alike.  The field had no reader.  This replaces
    it with a resolved, city-correct Activity id — or nothing.
    """

    if not activities:
        return None
    folded = text.casefold()
    for activity in activities:
        title = str(getattr(activity, "title", "") or "")
        if len(title) < 2:
            continue
        if title.casefold() in folded:
            return str(getattr(activity, "id", "")) or None
    return None


def decide_command(
    command: str,
    *,
    city_code: str,
    timezone: str,
    currency: str,
    locale: str = "",
    journey_state: str = "ACTIVE",
    activities: Sequence[Any] | None = None,
) -> CommandDecision:
    """Resolve one traveller command into a server-owned decision."""

    context = JourneyContext(
        city_code=str(city_code),
        timezone=str(timezone),
        currency=str(currency),
        locale=str(locale or ""),
        journey_state=str(journey_state or "ACTIVE"),
    )
    decision = route_message(command, context)

    creates_event = bool(decision.creates_real_event) and decision.intent in EVENT_INTENTS
    event_type: str | None = None
    severity: str | None = None
    if creates_event:
        event_type = resolve_event_type(command)
        if event_type is None:
            # A real personal disruption, but nothing the city-event vocabulary
            # can honestly represent.  Open the mission, file no city Event.
            creates_event = False
        else:
            severity = resolve_severity(command, event_type)

    return CommandDecision(
        intent=decision.intent,
        mutation_policy=decision.mutation_policy,
        requires_confirmation=bool(decision.requires_confirmation),
        creates_event=creates_event,
        event_type=event_type,
        severity=severity,
        affected_activity_id=_resolve_activity_hint(command, activities),
        confidence=float(decision.confidence),
        rationale=str(decision.rationale or ""),
        route=decision,
    )

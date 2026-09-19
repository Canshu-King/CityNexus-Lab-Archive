"""Traveller day-rhythm model.

The planner historically treated every traveller as the same 09:00-18:30
sightseer: candidate activities carry absolute clock times in the city fixture
and the overnight block is hard-coded to ``22:30 -> 06:30``.  Real travellers
have a body clock.

A couple who go to bed at 02:00 and wake at 11:00 are not served by a 09:30
museum slot, and a photographer who leaves the hotel at 04:00 is not served by
a 22:30 lights-out.  Neither case is a language-understanding problem: the
words are unambiguous, the *planner* simply has no representation for them.

This module supplies that representation and keeps it strictly advisory:

* :func:`extract_day_rhythm` reads a traveller's own words and returns a
  :class:`DayRhythm`, or ``None`` when the text says nothing about rhythm.
* :func:`rhythm_from_preferences` reads the same shape back out of persisted
  mission / preference JSON.
* :func:`apply_day_rhythm` filters candidate activity nodes against the waking
  window and re-times the overnight block.

Nothing here mutates authoritative state and nothing here is allowed to drop a
*locked* anchor (arrival, check-in, check-out, departure).  The rhythm can only
remove optional sightseeing and move the sleep block; it can never move a
commitment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Iterable, Sequence

__all__ = [
    "DayRhythm",
    "extract_day_rhythm",
    "rhythm_from_preferences",
    "apply_day_rhythm",
    "describe_day_rhythm",
]

#: A traveller who says nothing about rhythm keeps the historic defaults so the
#: behaviour of existing journeys is unchanged.
DEFAULT_WAKE_MINUTE = 7 * 60 + 30
DEFAULT_BED_MINUTE = 22 * 60 + 30


@dataclass(frozen=True)
class DayRhythm:
    """One traveller's waking window and meal pattern for a journey."""

    wake_minute: int
    bed_minute: int
    #: ``True`` when the traveller explicitly asked to skip breakfast.
    skip_breakfast: bool = False
    #: ``True`` when breakfast is replaced by a late brunch (implies skip).
    brunch: bool = False
    #: ``True`` when the traveller explicitly asked for late-night activity.
    late_night: bool = False
    #: Where the rhythm came from, for evidence and for the merge precedence.
    source: str = "DEFAULT"
    #: The exact substrings that produced the rhythm.
    evidence: tuple[str, ...] = ()

    @property
    def is_default(self) -> bool:
        return self.source == "DEFAULT"

    @property
    def overnight_minutes(self) -> int:
        """Minutes actually spent asleep, wrapping past midnight."""

        return (self.bed_minute - self.wake_minute) % (24 * 60)

    def as_dict(self) -> dict[str, Any]:
        return {
            "wake_minute": self.wake_minute,
            "bed_minute": self.bed_minute,
            "wake_hhmm": _hhmm(self.wake_minute),
            "bed_hhmm": _hhmm(self.bed_minute),
            "skip_breakfast": self.skip_breakfast,
            "brunch": self.brunch,
            "late_night": self.late_night,
            "source": self.source,
            "evidence": list(self.evidence),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DayRhythm | None":
        if not isinstance(raw, dict):
            return None
        try:
            wake = int(raw["wake_minute"])
            bed = int(raw["bed_minute"])
        except (KeyError, TypeError, ValueError):
            return None
        if not (0 <= wake < 24 * 60) or not (0 <= bed < 24 * 60):
            return None
        return cls(
            wake_minute=wake,
            bed_minute=bed,
            skip_breakfast=bool(raw.get("skip_breakfast", False)),
            brunch=bool(raw.get("brunch", False)),
            late_night=bool(raw.get("late_night", False)),
            source=str(raw.get("source", "PERSISTED")),
            evidence=tuple(str(item) for item in raw.get("evidence", []) or []),
        )


def _hhmm(minute: int) -> str:
    minute %= 24 * 60
    return f"{minute // 60:02d}:{minute % 60:02d}"


_NUMBER_TOKEN = r"(?:\d{1,2}(?::\d{2})?|[零〇一二两三四五六七八九十]+)"
_ZH_DIGITS = {
    "零": 0,
    "〇": 0,
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


def _clock_minute(token: str) -> int | None:
    """Parse ``11``, ``11:30``, ``十一点`` or ``两点`` into minutes past midnight.

    A bare hour without an explicit half is returned as ``hour * 60``; callers
    that need "around" semantics widen the window themselves.
    """

    token = token.strip()
    if not token:
        return None
    if ":" in token:
        hour, _, minute = token.partition(":")
        try:
            return (int(hour) % 24) * 60 + int(minute)
        except ValueError:
            return None
    if token.isdigit():
        hour = int(token)
        return (hour % 24) * 60 if hour <= 24 else None
    # Chinese numerals: only the shapes that actually appear in speech.
    if token == "十":
        return 10 * 60
    if token.startswith("十"):
        rest = _ZH_DIGITS.get(token[1:], None)
        return (10 + (rest or 0)) * 60
    if token.endswith("十"):
        head = _ZH_DIGITS.get(token[0], None)
        if head is None:
            return None
        return head * 10 * 60
    if len(token) == 2 and token[0] == "二" and token[1] in _ZH_DIGITS:
        # 二三 / 二五 style clock speech is rare; treat as tens+units.
        return (2 * 10 + _ZH_DIGITS[token[1]]) * 60
    value = _ZH_DIGITS.get(token)
    return value * 60 if value is not None else None


#: ``11 点才起`` / ``11点起床`` / ``11 点才睡醒``
_WAKE_PATTERNS = (
    re.compile(rf"({_NUMBER_TOKEN})\s*点\s*(?:才|多)?\s*(?:起|醒|起床|睡醒)"),
    re.compile(rf"({_NUMBER_TOKEN})\s*点\s*(?:才|多)?\s*(?:爬起|起来)"),
    re.compile(
        rf"(?:起床|睡醒|get\s+up|wake\s+up|waking\s+up)\s*(?:at|around|about)?\s*({_NUMBER_TOKEN})",
        re.IGNORECASE,
    ),
    re.compile(rf"(?:wake|get\s+up)\s*(?:at|around|about)\s*({_NUMBER_TOKEN})", re.IGNORECASE),
)

#: ``凌晨两点睡`` / ``2 点才睡`` / ``bed at 2``
_BED_PATTERNS = (
    re.compile(rf"(?:凌晨|半夜|晚上)?\s*({_NUMBER_TOKEN})\s*点\s*(?:才|多)?\s*(?:睡|睡觉|睡下|上床)"),
    re.compile(rf"({_NUMBER_TOKEN})\s*点\s*(?:才|多)?\s*(?:睡|睡觉)"),
    re.compile(
        rf"(?:bed|sleep|lights\s+out)\s*(?:at|around|about)?\s*({_NUMBER_TOKEN})",
        re.IGNORECASE,
    ),
)

_LATE_BED_PHRASES = (
    "很晚才睡",
    "折腾到很晚",
    "睡得很晚",
    "熬夜",
    "夜猫子",
    "stay up late",
    "late nights",
    "night owl",
    "sleep late",
)

_LATE_WAKE_PHRASES = (
    "起得很晚",
    "睡到中午",
    "中午才起",
    "睡到自然醒",
    "不爱早起",
    "不想早起",
    "sleep in",
    "lie in",
    "sleep until noon",
    "not a morning person",
    "no early mornings",
)

_NO_MORNING_PATTERNS = (
    re.compile(r"(?:别|不要|不用|不用给|别给|别再)\s*(?:给我)?\s*(?:排|安排|订)?"),
)

_SKIP_BREAKFAST_PHRASES = (
    "早餐不用",
    "不用订早餐",
    "不吃早餐",
    "不用早餐",
    "跳过早餐",
    "no breakfast",
    "skip breakfast",
    "without breakfast",
)

_BRUNCH_PHRASES = ("早午餐", "brunch", "brunch instead")

_LATE_NIGHT_PHRASES = (
    "夜宵",
    "夜市",
    "夜生活",
    "晚上还想出去",
    "夜游",
    "late night",
    "nightlife",
    "night market",
    "supper",
)

#: ``早上七八点`` — an approximate hour span.  Only the *earliest* bound is a
#: usable constraint, and only when the traveller says they do not want it.
_APPROX_MORNING = re.compile(rf"(?:早上|早晨|一大早|上午)?\s*({_NUMBER_TOKEN})\s*([七八五六])?\s*点")
_NEGATION_BEFORE = re.compile(r"(?:别|不要|不用|不想|拒绝|no|not|don't)\s*(?:给\s*我\s*)?(?:排|安排|订)?\s*$")


def _has_han(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def extract_day_rhythm(text: str) -> DayRhythm | None:
    """Read a traveller's waking window out of their own words.

    Returns ``None`` when the message says nothing about rhythm, so callers can
    keep the historic default rather than guessing.
    """

    if not text or not text.strip():
        return None
    lowered = text.casefold()
    evidence: list[str] = []

    wake: int | None = None
    for pattern in _WAKE_PATTERNS:
        match = pattern.search(text)
        if match:
            parsed = _clock_minute(match.group(1))
            if parsed is not None:
                wake = parsed
                evidence.append(match.group(0).strip())
                break

    bed: int | None = None
    for pattern in _BED_PATTERNS:
        match = pattern.search(text)
        if match:
            parsed = _clock_minute(match.group(1))
            if parsed is not None:
                bed = parsed
                evidence.append(match.group(0).strip())
                break

    late_bed = next((p for p in _LATE_BED_PHRASES if p in lowered), None)
    late_wake = next((p for p in _LATE_WAKE_PHRASES if p in lowered), None)
    if late_bed:
        evidence.append(late_bed)
    if late_wake:
        evidence.append(late_wake)

    # "别给我排早上七八点的行程" is a *negative* constraint on the morning.
    # It is weaker evidence than an explicit wake time, so it is only used to
    # widen an already-late rhythm or to justify a late default.
    morning_refusal: int | None = None
    for match in _APPROX_MORNING.finditer(text):
        prefix = text[: match.start()]
        if _NEGATION_BEFORE.search(prefix) or "别" in prefix[-6:] or "不要" in prefix[-8:]:
            earliest = _clock_minute(match.group(1))
            if earliest is not None:
                morning_refusal = earliest
                evidence.append(match.group(0).strip())
                break

    if wake is None and (late_wake or late_bed or morning_refusal is not None):
        # No explicit clock, but the traveller is unambiguous about sleeping in.
        wake = 10 * 60 + 30

    if bed is None and (late_bed or late_wake):
        # "晚上折腾到很晚才睡" with an 11:00 wake implies a small-hours bedtime.
        bed = 90  # 01:30

    if wake is None and bed is None:
        return None

    skip_breakfast = any(p in lowered for p in _SKIP_BREAKFAST_PHRASES)
    brunch = any(p in lowered for p in _BRUNCH_PHRASES)
    late_night = any(p in lowered for p in _LATE_NIGHT_PHRASES)

    if wake is None:
        # Only a bedtime was given; keep the default length of sleep.
        wake = (bed + (24 * 60 - DEFAULT_BED_MINUTE) + DEFAULT_WAKE_MINUTE) % (24 * 60)
    if bed is None:
        bed = (wake - DEFAULT_WAKE_MINUTE + DEFAULT_BED_MINUTE) % (24 * 60)

    if morning_refusal is not None and wake < morning_refusal:
        wake = morning_refusal

    if brunch:
        skip_breakfast = True

    return DayRhythm(
        wake_minute=wake % (24 * 60),
        bed_minute=bed % (24 * 60),
        skip_breakfast=skip_breakfast,
        brunch=brunch,
        late_night=late_night,
        source="EXTRACTED_FROM_USER_TEXT",
        evidence=tuple(dict.fromkeys(evidence)),
    )


def rhythm_from_preferences(preferences: Any) -> DayRhythm | None:
    """Read a persisted rhythm out of mission or traveller preferences."""

    if not isinstance(preferences, dict):
        return None
    raw = preferences.get("day_rhythm")
    if isinstance(raw, dict):
        return DayRhythm.from_dict(raw)
    return None


def describe_day_rhythm(rhythm: DayRhythm) -> str:
    """A short user-facing sentence, in the traveller's own language."""

    if _has_han(rhythm.evidence and "".join(rhythm.evidence) or ""):
        text = f"作息：{_hhmm(rhythm.wake_minute)} 起床，{_hhmm(rhythm.bed_minute)} 就寝"
        if rhythm.brunch:
            text += "，早餐改早午餐"
        elif rhythm.skip_breakfast:
            text += "，不排早餐"
        if rhythm.late_night:
            text += "，可安排夜间活动"
        return text
    text = f"Rhythm: awake {_hhmm(rhythm.wake_minute)}-{_hhmm(rhythm.bed_minute)}"
    if rhythm.brunch:
        text += ", brunch instead of breakfast"
    elif rhythm.skip_breakfast:
        text += ", no breakfast"
    if rhythm.late_night:
        text += ", late-night activity welcome"
    return text


def _is_optional_sightseeing(node: Any) -> bool:
    return not bool(getattr(node, "locked", False)) and str(
        getattr(node, "role", "")
    ) not in {"ARRIVAL", "DEPARTURE", "CHECK_IN", "CHECK_OUT", "LUGGAGE_DROP"}


def _in_waking_window(node: Any, rhythm: DayRhythm) -> bool:
    """True when an optional node falls inside the traveller's waking window."""

    start = datetime.fromisoformat(str(node.start_at))
    end = datetime.fromisoformat(str(node.end_at))
    minute = start.hour * 60 + start.minute
    end_minute = end.hour * 60 + end.minute
    if end.date() > start.date():
        end_minute += 24 * 60
    wake = rhythm.wake_minute
    bed = rhythm.bed_minute
    if bed <= wake:  # a small-hours bedtime wraps past midnight
        bed += 24 * 60
    if minute < wake:
        minute += 24 * 60
        end_minute += 24 * 60
    return minute >= wake and end_minute <= bed


def _is_breakfast(node: Any) -> bool:
    text = f"{getattr(node, 'title', '')} {getattr(node, 'place_key', '')}".casefold()
    return any(
        token in text
        for token in ("breakfast", "早餐", "morning set", "buffet")
    )


def apply_day_rhythm(
    nodes: Sequence[Any],
    rhythm: DayRhythm | None,
) -> list[Any]:
    """Filter optional activity nodes to the traveller's waking window.

    Locked anchors are always kept.  Optional sightseeing outside the window is
    dropped rather than moved, because the product has no evidence that a moved
    slot is actually open at the new time.
    """

    if rhythm is None or rhythm.is_default:
        return list(nodes)

    kept: list[Any] = []
    for node in nodes:
        role = str(getattr(node, "role", ""))
        if role == "STAY":
            kept.append(_retime_overnight(node, rhythm))
            continue
        if not _is_optional_sightseeing(node):
            kept.append(node)
            continue
        if _is_breakfast(node) and rhythm.skip_breakfast:
            continue
        if _in_waking_window(node, rhythm):
            kept.append(node)
    return kept


def _retime_overnight(node: Any, rhythm: DayRhythm) -> Any:
    """Move a synthetic overnight block onto the traveller's real bedtime."""

    start = datetime.fromisoformat(str(node.start_at))
    bed = start.replace(
        hour=rhythm.bed_minute // 60,
        minute=rhythm.bed_minute % 60,
        second=0,
        microsecond=0,
    )
    if bed < start - timedelta(hours=12):
        bed = bed + timedelta(days=1)
    end = bed + timedelta(minutes=rhythm.overnight_minutes)
    try:
        return replace(node, start_at=bed.isoformat(), end_at=end.isoformat())
    except TypeError:  # pragma: no cover - defensive for duck-typed nodes
        node.start_at = bed.isoformat()
        node.end_at = end.isoformat()
        return node


def merge_rhythms(*rhythms: DayRhythm | None) -> DayRhythm | None:
    """Later rhythms win, but an extracted rhythm never loses to a default."""

    result: DayRhythm | None = None
    for rhythm in rhythms:
        if rhythm is None:
            continue
        if result is None or not rhythm.is_default or result.is_default:
            result = rhythm
    return result

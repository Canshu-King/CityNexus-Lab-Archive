"""Canonical traveler capability and accessibility contract.

Capability interpretation is intentionally small and deterministic.  DeepSeek
may suggest items, but this module owns the vocabulary, severity defaults and
the conversion of explicit capability state into the existing Journey
constraint shape consumed by the feasibility gate.

The module is deliberately independent of FastAPI/SQLAlchemy so it can be
used by semantic compilation, planning and focused contract tests alike.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


CAPABILITY_CODES = (
    "STEP_FREE_REQUIRED",
    "AVOID_STAIRS",
    "MAX_WALKING_PER_LEG_M",
    "MAX_CONTINUOUS_WALKING_MIN",
    "MAX_DAILY_WALKING_M",
    "MIDDAY_REST_WINDOW",
    "REST_EVERY_MIN",
    "INFANT_NAP_WINDOW",
    "TOILET_BREAK_EVERY_MIN",
    "STROLLER",
    "LARGE_LUGGAGE",
    "SLOW_PACE",
    "QUIET_ENVIRONMENT",
    "INDOOR_PREFERRED",
    "SENSORY_LOW_STIMULATION",
)

CAPABILITY_CLASSES = (
    "HARD_ACCESSIBILITY_NEED",
    "CARE_REQUIREMENT",
    "PHYSICAL_LIMIT",
    "TRIP_CONTEXT",
    "SOFT_PREFERENCE",
)
CAPABILITY_SEVERITIES = ("HARD", "STRONG", "SOFT")
CAPABILITY_SCOPES = ("TRAVELER", "JOURNEY")
ACCESSIBILITY_STATES = (
    "ACCESSIBILITY_VERIFIED",
    "ACCESSIBILITY_UNVERIFIED",
    "ACCESSIBILITY_CONFLICT",
    "NEEDS_LIVE_EVIDENCE",
)

HARD_ACCESSIBILITY_CODES = frozenset({"STEP_FREE_REQUIRED", "AVOID_STAIRS"})
CARE_CODES = frozenset(
    {
        "MIDDAY_REST_WINDOW",
        "REST_EVERY_MIN",
        "INFANT_NAP_WINDOW",
        "TOILET_BREAK_EVERY_MIN",
    }
)
PHYSICAL_LIMIT_CODES = frozenset(
    {"MAX_WALKING_PER_LEG_M", "MAX_CONTINUOUS_WALKING_MIN", "MAX_DAILY_WALKING_M"}
)
CONTEXT_CODES = frozenset({"STROLLER", "LARGE_LUGGAGE"})
SOFT_CODES = frozenset(
    {"SLOW_PACE", "QUIET_ENVIRONMENT", "INDOOR_PREFERRED", "SENSORY_LOW_STIMULATION"}
)

_HARD_MARKERS = (
    "必须",
    "务必",
    "不能",
    "无法",
    "需要",
    "要求",
    "全程",
    "must",
    "cannot",
    "can't",
    "need",
    "required",
    "require",
    "no stairs",
    "step-free",
    "wheelchair",
)
_NEGATED_MARKERS = (
    "没有",
    "不需要",
    "不用",
    "无需",
    "不是",
    "以前",
    "曾经",
    "过去",
    "历史",
    "not wheelchair",
    "no wheelchair need",
    "used to",
    "historically",
    "可能",
    "也许",
    "据说",
    "朋友说",
    "传闻",
    "maybe",
    "might",
    "possibly",
    "allegedly",
)
_SPECULATIVE_MARKERS = ("说不定", "如果", "假如", "万一", "maybe", "might", "possibly", "perhaps", "if ")
_THIRD_PARTY_MARKERS = ("朋友说", "同事说", "我朋友", "我妈妈", "我父亲", "我父母", "我同事", "my friend", "my mother", "my father", "my parent", "my colleague", "a friend said")
_FACILITY_SUBJECT_MARKERS = ("车站", "机场", "酒店", "餐厅", "景点", "博物馆", "station", "airport", "hotel", "restaurant", "museum", "venue", "place")
_FIRST_PERSON_MARKERS = ("我", "本人", "i ", "i'm", "i am", "me", "my ")
_PERMANENCE_MARKERS = ("终身", "长期", "永久", "一辈子", "一直", "每次旅行", "以后每次", "不只是这次", "permanent", "permanently", "every trip", "every journey", "always", "not just this trip")
_THIS_TRIP_MARKERS = ("这次", "本次", "今天", "此次旅行", "this trip", "this journey", "just for today")


@dataclass(frozen=True)
class CapabilityItem:
    """A validated, serialisable capability item."""

    code: str
    capability_class: str
    severity: str
    params: Mapping[str, Any]
    scope: str = "JOURNEY"
    source: str = "SEMANTIC"
    provenance: str = "USER_STATED"
    explicit: bool = True
    active: bool = True
    confirmed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "class": self.capability_class,
            "severity": self.severity,
            "params": dict(self.params),
            "scope": self.scope,
            "source": self.source,
            "provenance": self.provenance,
            "explicit": self.explicit,
            "active": self.active,
            "confirmed": self.confirmed,
        }


def capability_class_for(code: str) -> str:
    code = str(code).upper()
    if code in HARD_ACCESSIBILITY_CODES:
        return "HARD_ACCESSIBILITY_NEED"
    if code in CARE_CODES:
        return "CARE_REQUIREMENT"
    if code in PHYSICAL_LIMIT_CODES:
        return "PHYSICAL_LIMIT"
    if code in CONTEXT_CODES:
        return "TRIP_CONTEXT"
    return "SOFT_PREFERENCE"


def default_severity(code: str, *, hard_asserted: bool = False) -> str:
    code = str(code).upper()
    if code in HARD_ACCESSIBILITY_CODES or code in PHYSICAL_LIMIT_CODES:
        return "HARD" if hard_asserted else "STRONG"
    if code in CARE_CODES:
        return "HARD" if hard_asserted else "STRONG"
    if code in CONTEXT_CODES:
        return "STRONG"
    return "SOFT"


def _bounded_number(value: Any, *, minimum: int = 0, maximum: int = 100_000) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number if minimum <= number <= maximum else None


def _time_window(value: str) -> tuple[str, str] | None:
    matches = re.findall(r"(?:[01]?\d|2[0-3])\s*[:：]\s*[0-5]?\d", value)
    if len(matches) < 2:
        # Also accept Chinese/English hour words in the common 13-15 shape.
        matches = re.findall(r"\b([01]?\d|2[0-3])\s*(?:点|時|h|hours?)\b", value, re.I)
    if len(matches) < 2:
        return None

    def normalise(item: str) -> str:
        raw = item.replace("：", ":").replace("点", ":00")
        if ":" not in raw:
            raw = f"{raw}:00"
        hour, minute = raw.split(":", 1)
        return f"{int(hour):02d}:{int(minute or 0):02d}"

    start, end = normalise(matches[0]), normalise(matches[1])
    sh, sm = (int(part) for part in start.split(":")); eh, em = (int(part) for part in end.split(":"))
    return (start, end) if eh * 60 + em > sh * 60 + sm else None


def _number_before(value: str, terms: Iterable[str]) -> int | None:
    unit = r"(?:公里|千米|km|kilomet(?:er|re)s?|米|公尺|m|分钟|分鐘|min|minutes?)"
    pattern = r"(?:" + "|".join(re.escape(term) for term in terms) + r").{0,18}?(-?[0-9]{1,8}(?:\.[0-9]+)?)\s*(" + unit + r")?"
    match = re.search(pattern, value, re.I)
    if not match: return None
    number = float(match.group(1)); unit_value = (match.group(2) or "").casefold()
    if number < 0: return None
    if unit_value in {"公里", "千米", "km", "kilometer", "kilometers", "kilometre", "kilometres"}: number *= 1000
    return _bounded_number(number)


def _hard_asserted(value: str) -> bool:
    return any(marker in value for marker in _HARD_MARKERS)


def extract_capabilities_from_text(
    text: str,
    *,
    scope: str = "JOURNEY",
    source: str = "SEMANTIC",
    provenance: str = "USER_STATED",
) -> tuple[dict[str, Any], ...]:
    """Extract bounded capability candidates from natural language.

    This is a conservative fallback and a post-model safety net.  It returns
    meaning only: no provider/evidence claim is generated here.  Negated or
    historical statements return no active capability for the matching clause.
    """

    raw_value = str(text or "").strip().casefold()
    if not raw_value:
        return ()
    effective_scope = scope if scope in CAPABILITY_SCOPES else "JOURNEY"
    if effective_scope == "JOURNEY" and any(marker in raw_value for marker in _PERMANENCE_MARKERS): effective_scope = "TRAVELER"
    elif any(marker in raw_value for marker in _THIS_TRIP_MARKERS): effective_scope = "JOURNEY"
    # Negation/rumour is clause-local.  A historical contrast may still carry
    # a current positive requirement in a later clause, so never discard the
    # entire message merely because one clause contains "used to" or "don't".
    clauses = [part.strip() for part in re.split(r"[,，。；;.!?！？\n]+|\bbut\b|\bhowever\b|但|但是|不过", raw_value) if part.strip()]
    active_clauses: list[str] = []
    for clause in clauses:
        negated = any(marker in clause for marker in _NEGATED_MARKERS) or bool(
            re.search(r"\b(?:don't|do not|doesn't|does not|not|never|no)\b", clause)
        )
        speculative = any(marker in clause for marker in _SPECULATIVE_MARKERS)
        third_party = any(marker in clause for marker in _THIRD_PARTY_MARKERS)
        first_person = any(marker in clause for marker in _FIRST_PERSON_MARKERS)
        facility_only = any(marker in clause for marker in _FACILITY_SUBJECT_MARKERS) and not first_person and any(token in clause for token in ("无障碍", "轮椅", "wheelchair", "accessible", "step-free", "step free"))
        explicit_limit = any(token in clause for token in ("不能超过", "最多走", "最多步行", "cannot walk more than", "walk no more than", "walking limit"))
        if speculative or third_party or facility_only: continue
        positive_need = any(marker in clause for marker in ("必须", "务必", "现在", "当前", "must", "now", "required", "need to"))
        if negated and not positive_need:
            if not explicit_limit:
                continue
        active_clauses.append(clause)
    value = " ".join(active_clauses)
    if not value:
        return ()
    hard = _hard_asserted(value)
    found: list[CapabilityItem] = []

    def add(code: str, params: Mapping[str, Any] | None = None, *, severity: str | None = None) -> None:
        if any(item.code == code for item in found):
            return
        found.append(
            CapabilityItem(
                code=code,
                capability_class=capability_class_for(code),
                severity=severity or default_severity(code, hard_asserted=hard),
                params=dict(params or {}),
                scope=effective_scope,
                source=source,
                provenance=provenance,
                explicit=True,
                active=True,
                confirmed=False,
            )
        )

    accessibility = any(
        token in value
        for token in ("无障碍", "轮椅", "wheelchair", "step-free", "step free", "accessible")
    )
    stairs = any(token in value for token in ("楼梯", "台阶", "stairs", "stair"))
    if accessibility and (hard or "全程" in value or "must" in value or "required" in value):
        add("STEP_FREE_REQUIRED", {"requirement": "step_free"})
    elif accessibility:
        add("STEP_FREE_REQUIRED", {"requirement": "step_free", "needs_confirmation": True}, severity="STRONG")
    if stairs and any(token in value for token in ("不能", "避免", "不要", "no ", "avoid", "cannot", "can't")):
        add("AVOID_STAIRS", {"avoid": True})

    walking = any(
        token in value
        for token in ("少走", "少步行", "不能走太多", "步行少", "走路少", "不能超过", "最多走", "最多步行", "low walking", "walk less", "avoid long walks", "avoid walking", "walking limit", "cannot walk more than", "walk no more than")
    )
    if walking:
        max_leg = _number_before(value, ("每段", "每程", "每腿", "每次", "per leg", "each leg", "under", "less than"))
        if max_leg is None:
            max_leg = _number_before(value, ("走", "walking", "walk"))
        add(
            "MAX_WALKING_PER_LEG_M",
            {"max_m": max_leg, "needs_clarification": max_leg is None},
            severity="HARD" if hard and max_leg is not None else "STRONG",
        )
    continuous = _number_before(value, ("连续", "持续", "continuous", "without a break"))
    if continuous is not None and any(token in value for token in ("走", "步行", "walking", "walk")):
        add("MAX_CONTINUOUS_WALKING_MIN", {"max_min": continuous}, severity="HARD" if hard else "STRONG")
    daily = _number_before(value, ("每天", "每日", "daily", "per day"))
    if daily is not None and any(token in value for token in ("米", "m ", "metre", "meter")):
        add("MAX_DAILY_WALKING_M", {"max_m": daily}, severity="HARD" if hard else "STRONG")

    window = _time_window(value)
    explicit_time_pair = len(re.findall(r"(?:[01]?\d|2[0-3])\s*[:：]\s*[0-5]?\d", value)) >= 2
    if any(token in value for token in ("午休", "中午休息", "midday rest", "midday break", "rest at noon")):
        params = ({"start": window[0], "end": window[1]} if window else {"needs_clarification": True} if explicit_time_pair else {"start": "12:00", "end": "14:00", "defaulted_window": True})
        add("MIDDAY_REST_WINDOW", params, severity="HARD" if hard and window else "STRONG")
    if any(token in value for token in ("午睡", "nap", "naptime")):
        add("INFANT_NAP_WINDOW", {"start": window[0] if window else "13:00", "end": window[1] if window else "15:00"}, severity="HARD" if hard else "STRONG")
    rest_every = _number_before(value, ("每", "every", "rest every"))
    if rest_every is not None and any(token in value for token in ("休息", "rest", "break")):
        add("REST_EVERY_MIN", {"interval_min": rest_every}, severity="HARD" if hard else "STRONG")
    toilet_every = _number_before(value, ("每", "every"))
    if toilet_every is not None and any(token in value for token in ("厕所", "卫生间", "toilet", "bathroom")):
        add("TOILET_BREAK_EVERY_MIN", {"interval_min": toilet_every}, severity="HARD" if hard else "STRONG")

    if any(token in value for token in ("婴儿车", "推车", "stroller", "buggy")):
        add("STROLLER", {"present": True})
    if any(token in value for token in ("大箱子", "行李", "luggage", "suitcase", "baggage")):
        add("LARGE_LUGGAGE", {"present": True})
    if any(token in value for token in ("慢一点", "慢速", "slow pace", "take it slowly")):
        add("SLOW_PACE", {"preferred": True})
    if any(token in value for token in ("安静", "quiet", "少刺激", "低刺激", "sensory", "low stimulation")):
        add("QUIET_ENVIRONMENT", {"preferred": True})
    if any(token in value for token in ("低刺激", "low stimulation", "sensory-friendly")):
        add("SENSORY_LOW_STIMULATION", {"preferred": True})
    if any(token in value for token in ("室内", "indoor")):
        add("INDOOR_PREFERRED", {"preferred": True})
    return tuple(item.as_dict() for item in found)


def canonicalize_capabilities(
    candidates: Iterable[Mapping[str, Any]] | None,
    *,
    source: str = "SEMANTIC",
    provenance: str = "USER_STATED",
    scope: str = "JOURNEY",
    explicit: bool | None = None,
    confirmed: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Validate model/API candidates and enforce hard-severity invariants."""

    result: list[dict[str, Any]] = []
    seen: dict[tuple[Any, str], dict[str, Any]] = {}
    for raw in candidates or ():
        if not isinstance(raw, Mapping):
            continue
        code = str(raw.get("code") or raw.get("rule_code") or "").upper().strip()
        if code not in CAPABILITY_CODES:
            continue
        klass = capability_class_for(code)
        raw_class = str(raw.get("class") or raw.get("capability_class") or klass).upper()
        if raw_class not in CAPABILITY_CLASSES:
            raw_class = klass
        params = raw.get("params") if isinstance(raw.get("params"), Mapping) else {}
        severity = str(raw.get("severity") or default_severity(code, hard_asserted=False)).upper()
        if severity not in CAPABILITY_SEVERITIES:
            severity = default_severity(code, hard_asserted=False)
        # A hard accessibility capability may not be downgraded by a model or
        # by an API client that mislabeled its class.
        # Accessibility requirements are never downgraded.  A structured
        # model candidate that identifies the requirement is sufficient to
        # preserve HARD semantics; only explicit negative/disputed language
        # is allowed to suppress the candidate before this boundary.
        if code in HARD_ACCESSIBILITY_CODES:
            severity = "HARD"
        item = CapabilityItem(
            code=code,
            capability_class=klass if code in HARD_ACCESSIBILITY_CODES else raw_class,
            severity=severity,
            params=dict(params),
            scope=str(raw.get("scope") or scope).upper() if str(raw.get("scope") or scope).upper() in CAPABILITY_SCOPES else "JOURNEY",
            source=str(raw.get("source") or source),
            provenance=str(raw.get("provenance") or provenance),
            explicit=bool(raw.get("explicit", True) if explicit is None else explicit),
            active=bool(raw.get("active", True)),
            confirmed=bool(raw.get("confirmed", confirmed)),
        )
        payload = item.as_dict()
        merge_key = (payload.get("scope"), code)
        previous = seen.get(merge_key)
        if previous is None:
            seen[merge_key] = payload
            result.append(payload)
        else:
            # Deterministic merge: HARD wins, then confirmed, then the first
            # stable parameter payload.  Duplicate codes never survive.
            if payload["severity"] == "HARD" or previous["severity"] != "HARD":
                previous["severity"] = payload["severity"]
            previous["confirmed"] = bool(previous.get("confirmed") or payload.get("confirmed"))
            incoming_params = dict(payload.get("params") or {}); existing_params = dict(previous.get("params") or {})
            for key in ("max_m", "max_min", "interval_min"):
                left = _bounded_number(existing_params.get(key), minimum=1); right = _bounded_number(incoming_params.get(key), minimum=1)
                if left is not None and right is not None: existing_params[key] = min(left, right)
                elif left is None and right is not None: existing_params[key] = right
            for key, value in incoming_params.items(): existing_params.setdefault(key, value)
            previous["params"] = existing_params
    return tuple(result)


def capability_constraints(capabilities: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """Translate active canonical capabilities into existing gate constraints."""

    constraints: list[dict[str, Any]] = []
    for item in canonicalize_capabilities(capabilities, source="CAPABILITY_PROJECTION"):
        if not item.get("active"):
            continue
        severity = str(item.get("severity") or "SOFT").upper()
        # Only HARD items are feasibility gates.  STRONG/SOFT remain available
        # to ranking and explanation through the original capability payload.
        if severity != "HARD":
            continue
        code = str(item["code"])
        params = dict(item.get("params") or {})
        constraints.append(
            {
                "kind": "HARD",
                "category": str(item.get("class") or capability_class_for(code)),
                "rule_code": code,
                "params": params,
                "active": True,
                "capability": item,
            }
        )
    return constraints


def summarize_capabilities(capabilities: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    items = [dict(item) for item in canonicalize_capabilities(capabilities)]
    return {
        "items": items,
        "hard": [item for item in items if item.get("severity") == "HARD"],
        "strong": [item for item in items if item.get("severity") == "STRONG"],
        "soft": [item for item in items if item.get("severity") == "SOFT"],
        "unknown_accessibility_is_not_accessible": True,
    }


def accessibility_state(value: Any) -> str:
    """Normalize provider/frozen accessibility metadata without inference."""

    if not isinstance(value, Mapping):
        return "ACCESSIBILITY_UNVERIFIED"
    status = str(value.get("evidence_status") or value.get("status") or "").upper()
    if status in ACCESSIBILITY_STATES:
        return status
    if status in {"VERIFIED", "KNOWN_ACCESSIBLE", "ACCESSIBLE", "TRUE"}:
        return "ACCESSIBILITY_VERIFIED"
    if status in {"CONFLICT", "KNOWN_INACCESSIBLE", "INACCESSIBLE", "FALSE", "STAIRS"}:
        return "ACCESSIBILITY_CONFLICT"
    if value.get("step_free") is True or value.get("wheelchair_access") is True:
        return "ACCESSIBILITY_VERIFIED"
    if value.get("step_free") is False or value.get("wheelchair_access") is False or value.get("stairs") is True:
        return "ACCESSIBILITY_CONFLICT"
    return "ACCESSIBILITY_UNVERIFIED"


def normalize_osm_tags(value: Any) -> dict[str, str]:
    """Accept provider tags as mappings or OSM-style key=value sequences."""
    if isinstance(value, Mapping):
        result: dict[str, str] = {}
        for key, raw in value.items():
            if isinstance(raw, (list, tuple, set)):
                raw = next((part for part in raw if not isinstance(part, (Mapping, list, tuple, set))), "")
            result[str(key).strip().lower()] = str(raw).strip().lower()
        return result
    result: dict[str, str] = {}
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, Mapping):
                result.update(normalize_osm_tags(item))
                continue
            text = str(item)
            if "=" in text:
                key, raw = text.split("=", 1)
                result[key.strip().lower()] = raw.strip().lower()
    return result


def evaluate_accessibility_requirement(code: str, facts: Any) -> str:
    """Evaluate only evidence that is about the requested requirement."""
    code = str(code).upper()
    if not isinstance(facts, Mapping):
        facts = {}
    tags = normalize_osm_tags(facts.get("osm_tags") or facts.get("tags") or facts)
    def truth(*keys: str) -> bool:
        return any(str(facts.get(key, "")).lower() in {"yes", "true", "1", "verified", "accessible"} for key in keys) or any(tags.get(key) in {"yes", "true", "1"} for key in keys)
    def false(*keys: str) -> bool:
        return any(str(facts.get(key, "")).lower() in {"no", "false", "0", "inaccessible", "stairs"} for key in keys) or any(tags.get(key) in {"no", "false", "0"} for key in keys)
    is_route = str(facts.get("subject") or facts.get("scope") or "").lower() in {"route", "path", "itinerary"}
    if code == "STEP_FREE_REQUIRED":
        step_count = facts.get("step_count", facts.get("steps"))
        highway_steps = tags.get("highway") == "steps"
        try: many_steps = int(step_count) > 0
        except (TypeError, ValueError): many_steps = False
        if truth("stairs", "has_stairs") or highway_steps or many_steps:
            return "ACCESSIBILITY_CONFLICT"
        if is_route and not truth("route_step_free", "step_free_route", "route_step_free_verified"):
            return "NEEDS_LIVE_EVIDENCE"
        if false("step_free", "step_free_verified"):
            return "ACCESSIBILITY_CONFLICT"
        if truth("step_free", "step_free_verified", "route_step_free", "step_free_route", "route_step_free_verified"):
            return "ACCESSIBILITY_VERIFIED"
        return "ACCESSIBILITY_UNVERIFIED"
    if code == "AVOID_STAIRS":
        if truth("stairs", "has_stairs"):
            return "ACCESSIBILITY_CONFLICT"
        if false("stairs", "has_stairs") or truth("step_free", "step_free_verified"):
            return "ACCESSIBILITY_VERIFIED"
        return "ACCESSIBILITY_UNVERIFIED"
    if code == "WHEELCHAIR_PLACE_ACCESS":
        if truth("wheelchair", "wheelchair_access"):
            return "ACCESSIBILITY_VERIFIED"
        if false("wheelchair", "wheelchair_access"):
            return "ACCESSIBILITY_CONFLICT"
    return accessibility_state(facts)

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
)


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

    return normalise(matches[0]), normalise(matches[1])


def _number_before(value: str, terms: Iterable[str]) -> int | None:
    pattern = r"(?:" + "|".join(re.escape(term) for term in terms) + r").{0,18}?([0-9]{1,6})\s*(?:米|公尺|m|分钟|分鐘|min|minutes?)?"
    match = re.search(pattern, value, re.I)
    return _bounded_number(match.group(1)) if match else None


def _hard_asserted(value: str) -> bool:
    return any(marker in value for marker in _HARD_MARKERS)


def _split_clauses(text: str) -> list[str]:
    """Split natural language into bounded clauses for negation scoping."""

    value = str(text or "").replace("；", ";").replace("，", ",")
    parts: list[str] = []
    for line in value.splitlines():
        for chunk in re.split(r"[。！？!?;]+", line):
            parts.extend(re.split(r"[,，]", chunk))
    return [part.strip() for part in parts if part.strip()]

def _extract_from_clause(
    clause: str,
    *,
    scope: str,
    source: str,
    provenance: str,
) -> list[dict[str, Any]]:
    value = str(clause or "").strip().casefold()
    if not value:
        return []
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
                scope=scope if scope in CAPABILITY_SCOPES else "JOURNEY",
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
    if accessibility:
        if hard or any(token in value for token in ("全程", "must", "required", "必须", "务必", "需要")):
            add("STEP_FREE_REQUIRED", {"requirement": "step_free"})
        else:
            add(
                "STEP_FREE_REQUIRED",
                {"requirement": "step_free", "needs_confirmation": True},
                severity="STRONG",
            )
    if stairs and any(token in value for token in ("不能", "避免", "不要", "no ", "avoid", "cannot", "can't", "不走")):
        add("AVOID_STAIRS", {"avoid": True})

    max_leg = _number_before(
        value,
        ("每段", "每程", "每腿", "每次", "per leg", "each leg", "最多", "不超过", "under", "less than"),
    )
    if max_leg is None and any(unit in value for unit in ("米", "meter", "metre", " m", "m ")):
        max_leg = _number_before(value, ("走", "步行", "walking", "walk"))
    walking = any(
        token in value
        for token in (
            "少走",
            "少步行",
            "不能走太多",
            "步行少",
            "走路少",
            "low walking",
            "walk less",
            "avoid long walks",
            "avoid walking",
            "walking limit",
            "走不动",
            "膝盖",
            "knee",
        )
    )
    if walking or max_leg is not None:
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
    midday_rest = (
        any(token in value for token in ("午休", "中午休息", "中午要休息", "midday rest", "midday break", "rest at noon"))
        or ("中午" in value and any(token in value for token in ("休息", "午休", "rest")))
    )
    if midday_rest:
        add(
            "MIDDAY_REST_WINDOW",
            {"start": window[0] if window else "12:00", "end": window[1] if window else "14:00"},
            severity="HARD" if hard else "STRONG",
        )
    if any(token in value for token in ("午睡", "nap", "naptime")):
        add(
            "INFANT_NAP_WINDOW",
            {"start": window[0] if window else "13:00", "end": window[1] if window else "15:00"},
            severity="HARD" if hard else "STRONG",
        )
    rest_every = _number_before(value, ("每", "every", "rest every"))
    if rest_every is not None and any(token in value for token in ("休息", "rest", "break")):
        add("REST_EVERY_MIN", {"max_min": rest_every}, severity="HARD" if hard else "STRONG")
    toilet_every = _number_before(value, ("每", "every"))
    if toilet_every is not None and any(token in value for token in ("厕所", "卫生间", "toilet", "bathroom")):
        add("TOILET_BREAK_EVERY_MIN", {"max_min": toilet_every}, severity="HARD" if hard else "STRONG")

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
    return [item.as_dict() for item in found]


def extract_capabilities_from_text(
    text: str,
    *,
    scope: str = "JOURNEY",
    source: str = "SEMANTIC",
    provenance: str = "USER_STATED",
) -> tuple[dict[str, Any], ...]:
    """Extract bounded capability candidates from natural language.

    Negation and historical statements are scoped to the clause that contains
    them.  For example, "以前不能走，现在想少走路" keeps the current low-walking
    candidate and does not let the historical clause suppress the whole text.
    """

    merged: dict[str, dict[str, Any]] = {}
    for clause in _split_clauses(text):
        folded = clause.casefold()
        if any(marker in folded for marker in _NEGATED_MARKERS):
            continue
        for item in _extract_from_clause(clause, scope=scope, source=source, provenance=provenance):
            code = str(item["code"])
            existing = merged.get(code)
            if existing is None or _severity_rank(item["severity"]) > _severity_rank(existing["severity"]):
                merged[code] = item
            else:
                merged[code] = {**existing, "params": {**existing.get("params", {}), **item.get("params", {})}}
    return tuple(merged.values())

def _severity_rank(value: str) -> int:
    return {"SOFT": 0, "STRONG": 1, "HARD": 2}.get(str(value).upper(), 0)


def canonicalize_capabilities(
    candidates: Iterable[Mapping[str, Any]] | None,
    *,
    source: str = "SEMANTIC",
    provenance: str = "USER_STATED",
    scope: str = "JOURNEY",
    explicit: bool | None = None,
    confirmed: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Validate model/API candidates and enforce hard-severity invariants.

    Resolution is deterministic when the same code appears more than once:
    parameters are merged, and the strongest severity wins (HARD > STRONG >
    SOFT).  A hard accessibility code cannot be downgraded unless the caller
    explicitly marked it as needing confirmation, in which case it is at least
    STRONG and still cannot become a quiet HARD fact.
    """

    merged: dict[str, CapabilityItem] = {}
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
        params = dict(params)
        raw_severity = str(raw.get("severity") or default_severity(code, hard_asserted=False)).upper()
        if raw_severity not in CAPABILITY_SEVERITIES:
            raw_severity = default_severity(code, hard_asserted=False)
        severity = raw_severity
        if code in HARD_ACCESSIBILITY_CODES:
            klass = capability_class_for(code)
            if bool(params.get("needs_confirmation")):
                # "I might need step-free access" is a candidate, not a
                # durable HARD fact.  It stays STRONG until the explicit
                # confirmation endpoint turns it into a HARD fact.
                severity = "STRONG"
            else:
                # The code itself is a hard accessibility requirement.  A
                # model/client cannot downgrade it to SOFT.
                severity = "HARD"
        item = CapabilityItem(
            code=code,
            capability_class=klass if code in HARD_ACCESSIBILITY_CODES else raw_class,
            severity=severity,
            params=params,
            scope=str(raw.get("scope") or scope).upper() if str(raw.get("scope") or scope).upper() in CAPABILITY_SCOPES else "JOURNEY",
            source=str(raw.get("source") or source),
            provenance=str(raw.get("provenance") or provenance),
            explicit=bool(raw.get("explicit", True) if explicit is None else explicit),
            active=bool(raw.get("active", True)),
            confirmed=bool(raw.get("confirmed", confirmed)),
        )
        existing = merged.get(code)
        if existing is None:
            merged[code] = item
            continue
        merged_params = {**dict(existing.params), **dict(item.params)}
        if _severity_rank(item.severity) > _severity_rank(existing.severity):
            merged[code] = CapabilityItem(
                code=item.code,
                capability_class=item.capability_class,
                severity=item.severity,
                params=merged_params,
                scope=item.scope,
                source=item.source,
                provenance=item.provenance,
                explicit=item.explicit or existing.explicit,
                active=item.active or existing.active,
                confirmed=item.confirmed or existing.confirmed,
            )
        else:
            merged[code] = CapabilityItem(
                code=existing.code,
                capability_class=existing.capability_class,
                severity=existing.severity,
                params=merged_params,
                scope=existing.scope,
                source=existing.source,
                provenance=existing.provenance,
                explicit=existing.explicit or item.explicit,
                active=existing.active or item.active,
                confirmed=existing.confirmed or item.confirmed,
            )
    return tuple(item.as_dict() for item in merged.values())

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


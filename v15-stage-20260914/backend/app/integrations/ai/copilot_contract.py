"""Semantic contract for the conversational travel copilot.

The model may improve interpretation, but this module keeps the intent
vocabulary, obvious fallback routing, and read-only what-if shape deterministic
at the server boundary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping


COPILOT_INTENTS = (
    "EXPLAIN_PLAN",
    "WHAT_IF",
    "DISCOVER",
    "PREFERENCE_CHANGE",
    "DISRUPTION_REPORT",
    "REPLAN_REQUEST",
    "UNKNOWN",
)

COPILOT_INTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["intent", "confidence", "reason", "entities"],
    "properties": {
        "intent": {"type": "string", "enum": list(COPILOT_INTENTS)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
        "entities": {"type": "object", "additionalProperties": True},
    },
}


@dataclass(frozen=True)
class VerifiedCopilotContext:
    journey_id: str
    journey_status: str
    reason_codes: tuple[str, ...]
    evidence: Mapping[str, Any]
    allowed_read_tools: tuple[str, ...] = (
        "get_journey",
        "get_journey_twin",
        "list_replans",
        "search_places",
    )

    def prompt_payload(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "journey_status": self.journey_status,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "allowed_read_tools": list(self.allowed_read_tools),
            "mutation_policy": "NO_DIRECT_STATE_MUTATION",
        }


@dataclass(frozen=True)
class CopilotSuggestion:
    text: str
    provider_key: str
    degraded: bool
    proposed_action: str | None = None


@dataclass(frozen=True)
class CopilotInterpretation:
    intent: str
    confidence: float
    reason: str
    entities: Mapping[str, Any]
    provider_key: str
    degraded: bool

    @property
    def mode(self) -> str:
        return "FALLBACK" if self.degraded else "AI"

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.intent,
            "confidence": self.confidence,
            "reason": self.reason,
            "entities": dict(self.entities),
            "provider": self.provider_key,
            "mode": self.mode,
        }


def _has_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def disruption_event_type(message: str) -> str | None:
    value = message.casefold()
    actual = _has_any(
        value,
        (
            "现在",
            "刚刚",
            "正在",
            "已经",
            "发生",
            "了",
            "currently",
            "right now",
            "just now",
            "is now",
            "has been",
            "there is",
        ),
    )
    if not actual:
        return None
    if _has_any(value, ("封路", "关闭", "进不去", "closed", "closure", "blocked")):
        return "CLOSURE"
    if _has_any(value, ("堵车", "拥堵", "交通管制", "封路", "traffic", "congestion", "road")):
        return "TRAFFIC_DELAY"
    if _has_any(value, ("延误", "晚点", "取消", "cancelled", "canceled", "delayed")):
        return "SCHEDULE_DELAY"
    if _has_any(value, ("下雨", "暴雨", "天气变", "raining", "rain", "storm", "weather")):
        return "WEATHER"
    return None


def classify_copilot_message(message: str) -> CopilotInterpretation:
    """Route obvious requests without treating preference text as an event."""

    value = message.casefold().strip()
    if not value:
        return CopilotInterpretation("UNKNOWN", 1.0, "empty message", {}, "deterministic", True)

    conditional_marker = _has_any(
        value,
        (
            "what if",
            "suppose",
            "would it",
            "would we",
            "would my",
            "会怎样",
            "会怎么样",
        ),
    )
    chinese_counterfactual = _has_any(value, ("如果", "假如", "要是")) and _has_any(
        value, ("会", "怎样", "怎么样", "能不能", "是否")
    ) and "就" not in value
    extension_question = bool(
        re.search(
            r"(?:多待|延长|stay(?:\s+at)?|extend|longer).{0,32}(?:会|怎样|how|what|minutes?|hours?)",
            value,
        )
    )
    if conditional_marker or chinese_counterfactual or extension_question:
        return CopilotInterpretation(
            "WHAT_IF", 0.98, "conditional or counterfactual language", {}, "deterministic", True
        )

    event_type = disruption_event_type(value)
    if event_type is not None:
        return CopilotInterpretation(
            "DISRUPTION_REPORT",
            0.97,
            f"reported current {event_type.lower()} reality",
            {"event_type": event_type},
            "deterministic",
            True,
        )

    if _has_any(value, ("为什么", "解释", "说明", "why", "explain", "how did", "tell me why")):
        return CopilotInterpretation(
            "EXPLAIN_PLAN", 0.96, "explanation request", {}, "deterministic", True
        )

    if _has_any(
        value,
        ("重新规划", "重新安排", "调整方案", "换方案", "replan", "reschedule", "change the plan"),
    ):
        return CopilotInterpretation(
            "REPLAN_REQUEST", 0.96, "explicit replanning request", {}, "deterministic", True
        )

    # A traveler can mix a preference with a direct plan edit. Removing a
    # scheduled activity is a replan request, not merely a soft preference;
    # keep that distinction visible to the existing confirmation path.
    if _has_any(
        value,
        (
            "去掉",
            "删掉",
            "移除",
            "取消上午",
            "删除活动",
            "不要排",
            "不排",
            "不安排",
            "不想安排",
            "remove",
            "drop",
            "skip",
            "don't schedule",
            "do not schedule",
            "no morning activities",
        ),
    ) and _has_any(
        value, ("活动", "上午", "下午", "行程", "安排", "计划", "activity", "morning", "itinerary", "plan")
    ):
        return CopilotInterpretation(
            "REPLAN_REQUEST", 0.96, "explicit activity or schedule edit", {}, "deterministic", True
        )

    if _has_any(value, ("找", "搜索", "推荐", "附近", "discover", "find", "search", "recommend")):
        return CopilotInterpretation(
            "DISCOVER", 0.93, "place or activity discovery request", {}, "deterministic", True
        )

    if _has_any(
        value,
        (
            "我想",
            "希望",
            "偏好",
            "少走",
            "少步行",
            "室内",
            "预算",
            "更喜欢",
            "prefer",
            "want",
            "like",
            "less walking",
            "under ",
            "more indoor",
            "就坐",
            "坐公交",
            "打车",
            "transit",
            "taxi",
        ),
    ):
        return CopilotInterpretation(
            "PREFERENCE_CHANGE",
            0.94,
            "traveler preference or constraint request",
            {},
            "deterministic",
            True,
        )

    return CopilotInterpretation("UNKNOWN", 0.72, "no supported semantic route matched", {}, "deterministic", True)


def parse_model_interpretation(raw_text: str) -> CopilotInterpretation | None:
    """Accept only the small structured contract returned by DeepSeek."""

    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL
        )
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        return None
    intent = str(parsed.get("intent") or "").upper()
    if intent not in COPILOT_INTENTS:
        return None
    confidence = float(parsed.get("confidence", 0.0))
    if not 0 <= confidence <= 1:
        return None
    entities = parsed.get("entities")
    if not isinstance(entities, dict):
        entities = {}
    return CopilotInterpretation(
        intent,
        confidence,
        str(parsed.get("reason") or "structured model interpretation"),
        entities,
        "deepseek",
        False,
    )


def what_if_parameters(message: str) -> dict[str, Any]:
    value = message.casefold()
    duration_minutes: int | None = None
    match = re.search(
        r"(?:多待|延长|stay(?:\s+at)?|extend|longer).{0,30}?(\d+)\s*(分钟|分|minutes?|mins?|小时|hours?|h)",
        value,
    )
    if match:
        amount = int(match.group(1))
        duration_minutes = amount * 60 if match.group(2).startswith(("小时", "hour", "h")) else amount
    elif re.search(r"(?:多待|延长|stay|extend).{0,12}(?:一个|一)小时", value):
        duration_minutes = 60
    elif re.search(r"(?:多待|延长|stay|extend).{0,12}半小时", value):
        duration_minutes = 30

    extra_cost_minor: int | None = None
    spend = re.search(
        r"(?:多花|增加预算|spend|pay|more).{0,24}?(?:¥|￥|元|cny|\$)?\s*(\d+)", value
    )
    if spend:
        extra_cost_minor = int(spend.group(1)) * 100

    return {
        "duration_minutes": duration_minutes,
        "extra_cost_minor": extra_cost_minor,
        "lower_walking": _has_any(value, ("少走", "少步行", "less walking", "walk less")),
        "indoor": _has_any(value, ("室内", "indoor")),
        "weather_or_closure": _has_any(
            value, ("下雨", "暴雨", "天气", "rain", "storm", "closed", "关闭", "封路", "堵车")
        ),
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _select_what_if_activity(
    message: str,
    activities: list[dict[str, Any]],
    *,
    current_activity_id: Any,
    protected_ids: list[str],
) -> dict[str, Any] | None:
    """Choose a flexible target without extending an arrival/commitment anchor."""

    value = message.casefold()
    for item in activities:
        title = str(item.get("title") or "").strip().casefold()
        if title and title in value:
            return item
    current = next(
        (item for item in activities if str(item.get("id")) == str(current_activity_id)),
        None,
    )
    if current is not None and not bool(current.get("locked")) and str(current.get("id")) not in protected_ids:
        return current
    return next(
        (
            item
            for item in activities
            if not bool(item.get("locked")) and str(item.get("id")) not in protected_ids
        ),
        current or (activities[0] if activities else None),
    )


def simulate_what_if(message: str, context: Mapping[str, Any]) -> dict[str, Any]:
    """Build a preview from selected-plan facts without writing any state."""

    parameters = what_if_parameters(message)
    plan = context.get("plan") if isinstance(context.get("plan"), dict) else None
    activities = list(plan.get("activities", [])) if plan else []
    legs = list(plan.get("legs", [])) if plan else []
    commitments = [item for item in context.get("commitments", []) if isinstance(item, dict)]
    protected_ids = [
        str(item.get("activity_id"))
        for item in commitments
        if item.get("protected") and item.get("activity_id")
    ]
    before_cost = int(plan.get("cost_minor", 0)) if plan else None
    before_walking = sum(int(item.get("walking_min") or 0) for item in legs) if plan else None
    before = {
        "plan_version_id": plan.get("id") if plan else None,
        "cost_minor": before_cost,
        "currency": plan.get("currency") if plan else context.get("currency"),
        "walking_min": before_walking,
        "activity_count": len(activities),
    }
    protected = {"count": len(protected_ids), "preserved": True, "ids": protected_ids}
    base: dict[str, Any] = {
        "simulation_only": True,
        "status": "NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE" if plan is None else "NEEDS_LIVE_EVIDENCE",
        "feasibility": "UNKNOWN",
        "before": before,
        "after": dict(before),
        "deltas": {"cost_minor": 0, "walking_min": 0, "schedule_drift_min": 0},
        "affected_activities": [],
        "protected_commitments": protected,
        "proposed_changes": [],
        "provenance": {
            "mode": "READ_ONLY_SIMULATION",
            "source_plan_version_id": plan.get("id") if plan else None,
            "provider_facts_reused": bool(plan and legs),
            "live_evidence_required": plan is None,
        },
        "explanation": "This preview does not change the selected plan, JourneyTwin, commitments, bookings, or payments.",
        "next_action": None,
    }
    if plan is None:
        return base

    if parameters["duration_minutes"] is not None:
        target = _select_what_if_activity(
            message,
            activities,
            current_activity_id=context.get("current_activity_id"),
            protected_ids=protected_ids,
        )
        if target is None:
            return base
        duration = int(parameters["duration_minutes"])
        target_id = str(target.get("id"))
        base["affected_activities"] = [
            {"id": target_id, "title": target.get("title"), "change": f"+{duration} min"}
        ]
        base["proposed_changes"] = [{"activity_id": target_id, "duration_delta_min": duration}]
        base["deltas"]["schedule_drift_min"] = duration
        if target_id in protected_ids or bool(target.get("locked")):
            base["status"] = "BLOCKED"
            base["feasibility"] = "BLOCKED"
            base["protected_commitments"]["preserved"] = False
            base["explanation"] = "The requested extension touches a protected or locked activity; no change was applied."
            base["provenance"]["live_evidence_required"] = False
            return base
        target_end = _parse_datetime(str(target.get("end_at") or ""))
        next_protected_start = min(
            (
                parsed
                for item in commitments
                if item.get("protected")
                for parsed in [_parse_datetime(str(item.get("scheduled_start_at") or ""))]
                if parsed is not None and target_end is not None and parsed >= target_end
            ),
            default=None,
        )
        if next_protected_start is not None and target_end is not None:
            if target_end + timedelta(minutes=duration) > next_protected_start:
                base["status"] = "BLOCKED"
                base["feasibility"] = "BLOCKED"
                base["protected_commitments"]["preserved"] = False
                base["explanation"] = "The extension would consume the next protected commitment window."
                return base
        base["status"] = "SIMULATED"
        base["feasibility"] = "PASS"
        base["after"]["schedule_drift_min"] = duration
        base["provenance"]["live_evidence_required"] = False
        base["explanation"] = "The selected activity can absorb this extension within the currently observed commitment window. Apply it only through an explicit replan request."
        base["next_action"] = "REQUEST_REPLAN"
        return base

    if parameters["extra_cost_minor"] is not None or parameters["lower_walking"] or parameters["indoor"]:
        base["status"] = "NEEDS_LIVE_EVIDENCE"
        base["next_action"] = "REQUEST_REPLAN"
        base["provenance"]["live_evidence_required"] = True
        if parameters["extra_cost_minor"] is not None:
            base["after"]["cost_minor"] = before_cost + int(parameters["extra_cost_minor"])
            base["deltas"]["cost_minor"] = int(parameters["extra_cost_minor"])
        if parameters["lower_walking"]:
            base["after"]["walking_min"] = None
            base["deltas"]["walking_min"] = None
        base["explanation"] = "A provider-backed alternative is required to prove the requested cost, walking, or indoor change; this read-only preview does not invent one."
        return base

    if parameters["weather_or_closure"]:
        base["status"] = "NEEDS_LIVE_EVIDENCE"
        base["next_action"] = "REQUEST_REPLAN"
        base["provenance"]["live_evidence_required"] = True
        base["explanation"] = "This is a hypothetical weather or closure scenario only. It is not recorded as a real event; an explicit replan can capture current provider evidence."
        return base

    return base


def validate_proposed_action(action: str | None) -> str | None:
    """Allow only explicit request-style actions; never direct domain mutation."""

    if action is None:
        return None
    allowed = {
        "REQUEST_REPLAN",
        "REQUEST_PREFERENCE_UPDATE",
        "REQUEST_PLAN_EXPLANATION",
        "REQUEST_PLACE_SEARCH",
    }
    if action not in allowed:
        raise ValueError(f"unsupported copilot action: {action}")
    return action

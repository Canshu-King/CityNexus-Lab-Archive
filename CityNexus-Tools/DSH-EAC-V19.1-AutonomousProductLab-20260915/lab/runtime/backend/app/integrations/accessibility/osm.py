"""Normalize OSM/provider accessibility tags without inference.

absent tag => NEEDS_LIVE_EVIDENCE; wheelchair=yes on a place => VERIFIED;
wheelchair=no / highway=steps => CONFLICT; ramp/elevator/kerb facts are
recorded but never promoted to a verified step-free route.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

ACCESSIBILITY_STATES = (
    "ACCESSIBILITY_VERIFIED",
    "ACCESSIBILITY_UNVERIFIED",
    "ACCESSIBILITY_CONFLICT",
    "NEEDS_LIVE_EVIDENCE",
)

SUBJECT_PLACE = "PLACE"
SUBJECT_ENTRANCE = "ENTRANCE"
SUBJECT_ROUTE = "ROUTE"
SUBJECT_TOILET = "TOILET"
SUBJECT_KERB = "KERB"
SUBJECT_VERTICAL = "VERTICAL_ACCESS"


@dataclass(frozen=True)
class AccessibilityEvidenceFact:
    state: str
    code: str
    subject: str
    summary: str
    raw_key: str | None
    raw_value: str | None
    provider: str
    source_key: str
    place_id: str | None = None
    city_code: str | None = None
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence_type: str = "tag_explicit"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "code": self.code,
            "subject": self.subject,
            "summary": self.summary,
            "raw": {"key": self.raw_key, "value": self.raw_value},
            "provider": self.provider,
            "source_key": self.source_key,
            "place_id": self.place_id,
            "city_code": self.city_code,
            "captured_at": self.captured_at,
            "confidence_type": self.confidence_type,
            "provenance": dict(self.provenance),
        }


def _text(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def _add(
    facts: list[AccessibilityEvidenceFact],
    *,
    state: str,
    code: str,
    subject: str,
    summary: str,
    raw_key: str | None,
    raw_value: Any,
    provider: str,
    source_key: str,
    place_id: str | None,
    city_code: str | None,
    captured_at: str,
    confidence_type: str,
) -> None:
    if state not in ACCESSIBILITY_STATES:
        state = "NEEDS_LIVE_EVIDENCE"
    facts.append(
        AccessibilityEvidenceFact(
            state=state,
            code=code,
            subject=subject,
            summary=summary,
            raw_key=raw_key,
            raw_value=None if raw_value is None else str(raw_value),
            provider=provider,
            source_key=source_key,
            place_id=place_id,
            city_code=city_code,
            captured_at=captured_at,
            confidence_type=confidence_type,
            provenance={
                "provider": provider,
                "source_key": source_key,
                "raw_key": raw_key,
                "raw_value": None if raw_value is None else str(raw_value),
                "captured_at": captured_at,
                "city_code": city_code,
                "place_id": place_id,
            },
        )
    )


def evidence_from_osm_tags(
    tags: Mapping[str, Any] | None,
    *,
    provider: str = "overpass",
    source_key: str = "unknown",
    place_id: str | None = None,
    city_code: str | None = None,
    captured_at: str | None = None,
) -> tuple[AccessibilityEvidenceFact, ...]:
    if not isinstance(tags, Mapping):
        tags = {}
    captured = captured_at or datetime.now(timezone.utc).isoformat()
    facts: list[AccessibilityEvidenceFact] = []

    def push(
        state: str,
        code: str,
        subject: str,
        summary: str,
        raw_key: str | None,
        raw_value: Any,
        confidence_type: str = "tag_explicit",
    ) -> None:
        _add(
            facts,
            state=state,
            code=code,
            subject=subject,
            summary=summary,
            raw_key=raw_key,
            raw_value=raw_value,
            provider=provider,
            source_key=source_key,
            place_id=place_id,
            city_code=city_code,
            captured_at=captured,
            confidence_type=confidence_type,
        )

    wheelchair = _text(tags.get("wheelchair"))
    entrance_wheelchair = _text(tags.get("entrance:wheelchair") or tags.get("wheelchair:entrance"))
    highway = _text(tags.get("highway"))
    steps = _text(tags.get("steps"))
    step_count = tags.get("step_count")
    toilet_wheelchair = _text(tags.get("toilets:wheelchair"))
    ramp = _text(tags.get("ramp") or tags.get("ramp:wheelchair"))
    elevator = _text(tags.get("elevator") or tags.get("highway:elevator"))
    kerb = _text(tags.get("kerb"))
    tactile = _text(tags.get("tactile_paving"))
    has_step_conflict = (
        highway == "steps"
        or steps in {"yes", "true"}
        or step_count not in (None, "", 0, "0")
    )

    if wheelchair in {"yes", "designated", "true"}:
        push("ACCESSIBILITY_VERIFIED", "WHEELCHAIR_ACCESS", SUBJECT_PLACE,
             "OSM wheelchair=yes is explicit provider evidence for this place.",
             "wheelchair", tags.get("wheelchair"))
    elif wheelchair in {"no", "false", "not_accessible"}:
        push("ACCESSIBILITY_CONFLICT", "WHEELCHAIR_ACCESS", SUBJECT_PLACE,
             "OSM wheelchair=no is an explicit conflict for wheelchair access.",
             "wheelchair", tags.get("wheelchair"))
    elif wheelchair in {"limited", "partial"}:
        push("ACCESSIBILITY_UNVERIFIED", "WHEELCHAIR_ACCESS", SUBJECT_PLACE,
             "OSM wheelchair=limited is not a verified step-free claim.",
             "wheelchair", tags.get("wheelchair"), "tag_limited")

    if entrance_wheelchair in {"yes", "designated", "true"}:
        push("ACCESSIBILITY_VERIFIED", "ENTRANCE_STEP_FREE", SUBJECT_ENTRANCE,
             "Explicit entrance:wheelchair=yes evidence.",
             "entrance:wheelchair", tags.get("entrance:wheelchair") or tags.get("wheelchair:entrance"))
    elif entrance_wheelchair in {"no", "false"}:
        push("ACCESSIBILITY_CONFLICT", "ENTRANCE_STEP_FREE", SUBJECT_ENTRANCE,
             "Explicit entrance:wheelchair=no evidence.",
             "entrance:wheelchair", tags.get("entrance:wheelchair") or tags.get("wheelchair:entrance"))

    if highway == "steps":
        push("ACCESSIBILITY_CONFLICT", "STAIRS", SUBJECT_ROUTE,
             "OSM explicitly records steps; this conflicts with step-free access.",
             "highway", tags.get("highway"))
    if steps in {"yes", "true"}:
        push("ACCESSIBILITY_CONFLICT", "STAIRS", SUBJECT_ROUTE,
             "OSM steps=yes is an explicit stair conflict.",
             "steps", tags.get("steps"))
    if step_count not in (None, "", 0, "0"):
        push("ACCESSIBILITY_CONFLICT", "STEP_COUNT", SUBJECT_ROUTE,
             f"OSM step_count={step_count} is an explicit stair conflict.",
             "step_count", step_count)

    if toilet_wheelchair in {"yes", "designated", "true"}:
        push("ACCESSIBILITY_VERIFIED", "ACCESSIBLE_TOILET", SUBJECT_TOILET,
             "OSM toilets:wheelchair=yes is explicit evidence for an accessible toilet.",
             "toilets:wheelchair", tags.get("toilets:wheelchair"))
    elif toilet_wheelchair in {"no", "false"}:
        push("ACCESSIBILITY_CONFLICT", "ACCESSIBLE_TOILET", SUBJECT_TOILET,
             "OSM toilets:wheelchair=no is an explicit conflict.",
             "toilets:wheelchair", tags.get("toilets:wheelchair"))

    if ramp:
        push("ACCESSIBILITY_UNVERIFIED", "RAMP_PRESENT", SUBJECT_VERTICAL,
             "A ramp tag exists, but it does not prove a step-free route to the entrance.",
             "ramp" if tags.get("ramp") is not None else "ramp:wheelchair",
             tags.get("ramp") if tags.get("ramp") is not None else tags.get("ramp:wheelchair"),
             "tag_partial")
    if elevator:
        push("ACCESSIBILITY_UNVERIFIED", "ELEVATOR_PRESENT", SUBJECT_VERTICAL,
             "An elevator tag exists, but route access and operating status are not verified.",
             "elevator" if tags.get("elevator") is not None else "highway:elevator",
             tags.get("elevator") if tags.get("elevator") is not None else tags.get("highway:elevator"),
             "tag_partial")
    if kerb:
        push("ACCESSIBILITY_UNVERIFIED", "KERB_EVIDENCE", SUBJECT_KERB,
             "Kerb metadata is segment-level and does not prove the whole route.",
             "kerb", tags.get("kerb"), "tag_partial")
    if tactile:
        push("ACCESSIBILITY_UNVERIFIED", "TACTILE_PAVING", SUBJECT_ROUTE,
             "Tactile paving metadata is partial route evidence.",
             "tactile_paving", tags.get("tactile_paving"), "tag_partial")

    if wheelchair in {"yes", "designated", "true"} and has_step_conflict:
        push("ACCESSIBILITY_CONFLICT", "CONFLICTING_TAGS", SUBJECT_PLACE,
             "Provider tags conflict: wheelchair=yes with explicit stairs/step_count.",
             "wheelchair", tags.get("wheelchair"), "tag_conflict")

    relevant = any(
        value not in ("", "none")
        for value in (wheelchair, entrance_wheelchair, highway, steps, ramp, elevator, kerb, tactile)
    ) or step_count not in (None, "", 0, "0") or toilet_wheelchair not in ("",)
    if not relevant and not facts:
        push("NEEDS_LIVE_EVIDENCE", "ACCESSIBILITY_DATA", SUBJECT_PLACE,
             "No relevant accessibility tags were present; this is unknown, not accessible.",
             None, None, "tag_absent")
    return tuple(facts)


def evidence_from_overpass_candidate(candidate: Any) -> tuple[AccessibilityEvidenceFact, ...]:
    metadata = getattr(candidate, "metadata", None) or getattr(candidate, "evidence", {}) or {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    tags = metadata.get("tags") if isinstance(metadata.get("tags"), Mapping) else metadata
    source_key = str(getattr(candidate, "external_id", None) or getattr(candidate, "semantic_key", "unknown"))
    name = str(getattr(candidate, "name", "") or "")
    city_code = str(getattr(candidate, "city_code", "") or "") or None
    facts = evidence_from_osm_tags(
        tags,
        provider=str(getattr(candidate, "provider_key", "overpass") or "overpass"),
        source_key=source_key,
        place_id=source_key,
        city_code=city_code,
    )
    if not name:
        return facts
    return tuple(
        AccessibilityEvidenceFact(
            state=fact.state,
            code=fact.code,
            subject=fact.subject,
            summary=f"{name}: {fact.summary}",
            raw_key=fact.raw_key,
            raw_value=fact.raw_value,
            provider=fact.provider,
            source_key=fact.source_key,
            place_id=fact.place_id,
            city_code=fact.city_code,
            captured_at=fact.captured_at,
            confidence_type=fact.confidence_type,
            provenance={**dict(fact.provenance), "place_name": name},
        )
        for fact in facts
    )


def overall_accessibility_state(facts: Iterable[Any]) -> str:
    """Conservative aggregate state across provider facts.

    Any conflict wins, then any missing evidence, then any partial/unverified
    fact.  Only an all-verified set becomes ACCESSIBILITY_VERIFIED.
    """

    states: set[str] = set()
    for fact in facts:
        if isinstance(fact, Mapping):
            states.add(str(fact.get("state")))
        else:
            states.add(str(getattr(fact, "state", "NEEDS_LIVE_EVIDENCE")))
    if "ACCESSIBILITY_CONFLICT" in states:
        return "ACCESSIBILITY_CONFLICT"
    if "NEEDS_LIVE_EVIDENCE" in states:
        return "NEEDS_LIVE_EVIDENCE"
    if "ACCESSIBILITY_UNVERIFIED" in states:
        return "ACCESSIBILITY_UNVERIFIED"
    if "ACCESSIBILITY_VERIFIED" in states:
        return "ACCESSIBILITY_VERIFIED"
    return "NEEDS_LIVE_EVIDENCE"

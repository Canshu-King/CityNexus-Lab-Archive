"""Anchor-aware template scheduling.

A confirmed ``C4_Anchored`` commitment is a *requirement to build around*, not
only a veto.  This module resolves each active anchor to a concrete, routable
``Place`` identity and pins it into a candidate schedule before the deterministic
gate runs.  Optional POIs are re-timed around the anchor and dropped rather than
allowed to breach the journey window.

The shape mirrors ``app.planning.authoritative_v12``: ARRIVAL / DEPARTURE use the
structural node keys ``arrival-anchor`` / ``departure-anchor`` and the concrete
Place id ``v12:{journey_id}:{key}``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CityService, Commitment, Journey, Place
from app.planning.anchors import (
    ARRIVAL_ROLE,
    DEPARTURE_ROLE,
    MID_TRIP_ROLE,
    STRUCTURAL_ANCHOR_KEYS,
    normalise_role,
    structural_external_id,
    structural_place_id,
)

ANCHOR_PROVIDER_KEY = "citynexus-v12-authoritative"
# A structural anchor occupies a bounded slot so a later leg cannot overlap it.
ANCHOR_DURATION_MIN = 20
# Deterministic fixture default when a pair is not frozen yet.
DEFAULT_TRAVEL_MIN = 20


@dataclass(frozen=True)
class CandidateActivity:
    """One scheduled candidate activity (gate + persistence share this shape)."""

    place_id: str
    title: str
    start_at: datetime
    end_at: datetime
    cost_minor: int = 0
    locked: bool = False
    anchor_role: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedAnchor:
    """A C4 anchor resolved to a concrete Place identity."""

    role: str
    semantic_key: str
    place_id: str
    place: Place
    scheduled_at: datetime
    time_boundary: str


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(value: Any, default: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        return parsed if isinstance(parsed, type(default)) else default
    return default


def active_c4_commitments(session: Session, journey: Journey) -> list[Commitment]:
    return list(
        session.scalars(
            select(Commitment).where(
                Commitment.journey_id == journey.id,
                Commitment.status == "ACTIVE",
                Commitment.level == "C4_Anchored",
            )
        ).all()
    )


def _city_center(session: Session, journey: Journey) -> tuple[float, float]:
    first = session.scalar(
        select(Place).where(Place.city_code == journey.city_code).limit(1)
    )
    if first is not None:
        return float(first.latitude), float(first.longitude)
    return 0.0, 0.0


def _structural_place(session: Session, journey: Journey, role: str) -> Place:
    """Materialise (or reuse) the structural anchor Place, matching V12's identity."""

    external_id = structural_external_id(journey.id, role)
    row = session.scalar(
        select(Place).where(
            Place.provider_key == ANCHOR_PROVIDER_KEY,
            Place.external_id == external_id,
        )
    )
    if row is not None:
        return row
    place_id = structural_place_id(journey.id, role)
    row = session.get(Place, place_id)
    if row is not None:
        return row
    latitude, longitude = _city_center(session, journey)
    offset = -0.015 if role == ARRIVAL_ROLE else 0.06
    offset_lon = -0.02 if role == ARRIVAL_ROLE else 0.08
    row = Place(
        id=place_id,
        provider_key=ANCHOR_PROVIDER_KEY,
        external_id=external_id,
        city_code=journey.city_code,
        name="Arrival" if role == ARRIVAL_ROLE else "Departure",
        category=role.lower(),
        latitude=latitude + offset,
        longitude=longitude + offset_lon,
        opening_hours_json=_json({"status": "NORMALIZED", "always_available": True}),
        tags_json=_json(["v12-authoritative", role.lower()]),
        metadata_json=_json({"anchor": role, "available": True, "cost_minor": 0}),
        updated_at=datetime.now().astimezone().isoformat(),
    )
    session.add(row)
    session.flush()
    return row


def resolve_plan_anchors(
    session: Session, journey: Journey
) -> tuple[list[ResolvedAnchor], list[str]]:
    """Resolve active C4 anchors; returns (resolved, unresolved_descriptions)."""

    resolved: list[ResolvedAnchor] = []
    unresolved: list[str] = []
    for commitment in active_c4_commitments(session, journey):
        policy = _load(commitment.policy_json, {})
        role = normalise_role(policy.get("anchor_role"))
        if not role:
            # A booking/order C4 anchor binds a concrete Activity, not a
            # planner node; it is protected through activity_id instead.
            continue
        raw_key = str(policy.get("semantic_key") or "").strip()
        scheduled = str(policy.get("scheduled_start_at") or "").strip()
        if not scheduled:
            unresolved.append(f"{role}:NO_SCHEDULED_START")
            continue
        try:
            scheduled_at = datetime.fromisoformat(scheduled)
        except ValueError:
            unresolved.append(f"{role}:INVALID_SCHEDULED_START")
            continue
        if role in (ARRIVAL_ROLE, DEPARTURE_ROLE):
            place = _structural_place(session, journey, role)
            resolved.append(
                ResolvedAnchor(
                    role=role,
                    semantic_key=structural_place_id(journey.id, role),
                    place_id=place.id,
                    place=place,
                    scheduled_at=scheduled_at,
                    time_boundary="END" if role == DEPARTURE_ROLE else "START",
                )
            )
            continue
        place = session.get(Place, raw_key)
        if place is None:
            service = session.get(CityService, raw_key)
            if service is not None and service.place_id:
                place = session.get(Place, service.place_id)
        if place is None or place.city_code != journey.city_code:
            unresolved.append(f"{role}:{raw_key}")
            continue
        resolved.append(
            ResolvedAnchor(
                role=MID_TRIP_ROLE,
                semantic_key=raw_key,
                place_id=place.id,
                place=place,
                scheduled_at=scheduled_at,
                time_boundary="START",
            )
        )
    return resolved, unresolved


def _place_cost(place: Place) -> int:
    metadata = _load(place.metadata_json, {})
    try:
        return int(metadata.get("cost_minor", 0))
    except (TypeError, ValueError):
        return 0


def _place_duration(place: Place) -> int:
    metadata = _load(place.metadata_json, {})
    try:
        return max(15, int(metadata.get("duration_min", 60)))
    except (TypeError, ValueError):
        return 60


def _template_start(journey_start: datetime, text: str) -> datetime:
    hour, minute = (int(part) for part in str(text).split(":", 1))
    return journey_start.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _merge_anchors(
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
) -> list[CandidateActivity]:
    """Interleave anchors with template POIs in chronological order."""

    optional: list[CandidateActivity] = []
    for place_id, title, start_text, end_text in template:
        if place_id not in places:
            continue
        if any(place_id == anchor.place_id for anchor in anchors):
            continue
        place = places[place_id]
        optional.append(
            CandidateActivity(
                place_id=place_id,
                title=title,
                start_at=_template_start(journey_start, start_text),
                end_at=_template_start(journey_start, end_text),
                cost_minor=_place_cost(place),
                locked=place_id == "place-river-cruise",
            )
        )
    anchor_rows: list[CandidateActivity] = []
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
        )
        if anchor.time_boundary == "END":
            start_at = anchor.scheduled_at - timedelta(minutes=duration)
            end_at = anchor.scheduled_at
        else:
            start_at = anchor.scheduled_at
            end_at = anchor.scheduled_at + timedelta(minutes=duration)
        anchor_rows.append(
            CandidateActivity(
                place_id=anchor.place_id,
                title=anchor.place.name,
                start_at=start_at,
                end_at=end_at,
                cost_minor=_place_cost(anchor.place),
                locked=True,
                anchor_role=anchor.role,
                metadata={
                    "semantic_key": anchor.semantic_key,
                    "anchor_role": anchor.role,
                    "commitment_anchor": True,
                },
            )
        )
    return sorted(
        [*optional, *anchor_rows],
        key=lambda item: (item.start_at, 0 if item.anchor_role else 1, item.place_id),
    )


def _estimate_gap_minutes(
    travel_minutes: Mapping[tuple[str, str], int] | None,
    origin: str | None,
    destination: str | None,
) -> int:
    """Frozen travel time for one leg, or the deterministic fixture default."""

    if not origin or not destination:
        return 0
    if travel_minutes is not None:
        value = travel_minutes.get((origin, destination))
        if value is not None:
            return int(value)
    return DEFAULT_TRAVEL_MIN


def schedule_template_with_anchors(
    *,
    journey: Journey,
    template: Sequence[tuple[str, str, str, str]],
    places: Mapping[str, Place],
    anchors: Sequence[ResolvedAnchor],
    journey_start: datetime,
    journey_end: datetime,
    travel_minutes: Mapping[tuple[str, str], int] | None = None,
) -> list[CandidateActivity] | None:
    """Return a candidate schedule, or ``None`` when the anchor cannot be met.

    Anchors are pinned to their exact required time.  Optional template POIs are
    re-timed around them; any POI that would overlap an anchor or leave the
    journey window is dropped instead of corrupting the plan.
    """

    if not anchors:
        schedule: list[CandidateActivity] = []
        for place_id, title, start_text, end_text in template:
            if place_id not in places:
                return None
            place = places[place_id]
            schedule.append(
                CandidateActivity(
                    place_id=place_id,
                    title=title,
                    start_at=_template_start(journey_start, start_text),
                    end_at=_template_start(journey_start, end_text),
                    cost_minor=_place_cost(place),
                    locked=place_id == "place-river-cruise",
                )
            )
        return schedule

    ordered = _merge_anchors(template, places, anchors, journey_start)
    if not ordered:
        return None
    schedule: list[CandidateActivity] = []
    cursor: datetime | None = None
    previous_place: str | None = None
    for item in ordered:
        gap = (
            _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
            if previous_place
            else 0
        )
        if item.anchor_role is not None:
            # Drop optional POIs that could not arrive before the anchor starts.
            while schedule and cursor is not None:
                needed = _estimate_gap_minutes(
                    travel_minutes, previous_place, item.place_id
                )
                if cursor + timedelta(minutes=needed) <= item.start_at:
                    break
                schedule.pop()
                cursor = schedule[-1].end_at if schedule else None
                previous_place = schedule[-1].place_id if schedule else None
            if cursor is not None:
                needed = _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
                if cursor + timedelta(minutes=needed) > item.start_at:
                    return None
            schedule.append(item)
            cursor = item.end_at
            previous_place = item.place_id
            continue
        start_at = max(item.start_at, cursor + timedelta(minutes=gap)) if cursor is not None else item.start_at
        duration = item.end_at - item.start_at
        end_at = start_at + duration
        if end_at > journey_end:
            # Cannot fit before the journey ends: drop this optional POI.
            continue
        schedule.append(
            CandidateActivity(
                place_id=item.place_id,
                title=item.title,
                start_at=start_at,
                end_at=end_at,
                cost_minor=item.cost_minor,
                locked=item.locked,
                anchor_role=None,
                metadata=item.metadata,
            )
        )
        cursor = end_at
        previous_place = item.place_id
    for item in schedule:
        if item.start_at < journey_start or item.end_at > journey_end:
            return None
    return schedule


def anchor_assignment_for_activities(
    activities: Sequence[Any],
    anchors: Sequence[ResolvedAnchor],
) -> dict[str, str]:
    """Map commitment semantic keys to the Activity ids that satisfy them."""

    assigned: dict[str, str] = {}
    for anchor in anchors:
        match = next(
            (
                item
                for item in activities
                if str(getattr(item, "place_id", None) or "") == anchor.place_id
            ),
            None,
        )
        if match is not None:
            assigned[anchor.semantic_key] = match.id
    return assigned


def effective_journey_window(
    journey: Journey,
    anchors: Sequence[ResolvedAnchor],
) -> tuple[str, str]:
    """Widen the draft journey window to contain every confirmed C4 anchor.

    A confirmed reservation is an authoritative real-world fact.  A draft
    journey window ("09:00-19:00") must never make a booked 08:00 departure
    unplannable; the window expands to contain the commitment instead.  The same
    helper is used by generation *and* revalidation so the two never disagree.
    """

    start = datetime.fromisoformat(str(journey.start_at))
    end = datetime.fromisoformat(str(journey.end_at))
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
        )
        candidate_start, candidate_end = anchor_window(
            anchor.role, anchor.scheduled_at, duration
        )
        if candidate_start < start:
            start = candidate_start
        if candidate_end > end:
            end = candidate_end
    return start.isoformat(), end.isoformat()


def anchor_window(
    role: str,
    scheduled_at: datetime,
    duration_min: int = 20,
) -> tuple[datetime, datetime]:
    """The real-world time span a C4 anchor occupies.

    A DEPARTURE anchor constrains the END of its activity, so the span starts
    ``duration_min`` before the booked departure.  Everything else is anchored
    on its START.
    """

    delta = timedelta(minutes=max(1, int(duration_min)))
    if normalise_role(role) == DEPARTURE_ROLE:
        return scheduled_at - delta, scheduled_at
    return scheduled_at, scheduled_at + delta

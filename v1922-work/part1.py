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

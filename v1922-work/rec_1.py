"""Durable mid-trip HARD capability recovery.

A newly confirmed HARD capability on an ACTIVE journey invalidates the active
plan.  The consequence must be *durable state*, not a JSON field buried in one
response:

    new HARD capability invalidates active plan
      -> durable Event + recovery state on the Journey
      -> C4 commitments preserved
      -> governed ReplanProposal, or an explicit no-alternative state
      -> visible frontend recovery action

Two invariants are load-bearing:

1. **Acknowledgement is not resolution.**  ``Event.status = ACKNOWLEDGED``
   records that the traveller saw the warning.  It never marks an infeasible
   plan safe, never hides the journey truth, and never lets stale evidence look
   current.  Only a revalidated feasible replacement resolves recovery.
2. **No-alternative is a persisted fact.**  ``RECOVERY_REQUIRED_NO_ALTERNATIVE``
   is written only after an actual replan attempt produced zero feasible
   candidates.  It is never inferred from a missing boolean.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event, Journey, PlanVersion

# Durable recovery is a user-initiated change to the active journey.
# Event.event_type is a closed vocabulary (schema.sql), so the specific
# recovery kind is carried in the payload rather than inventing a new type.
EVENT_TYPE = "USER_CHANGE"
# Distinguishes recovery events from any other user-initiated change event.
PROVIDER_KEY = "citynexus-capability-recovery"
RECOVERY_KIND = "CAPABILITY_HARD_RECOVERY"
ACTIVE = "RECOVERY_REQUIRED"
NO_ALTERNATIVE = "RECOVERY_REQUIRED_NO_ALTERNATIVE"
RESOLVED = "RESOLVED"
ACKNOWLEDGED = "ACKNOWLEDGED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(value: Any, default: Any) -> Any:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        return parsed if isinstance(parsed, dict) else default
    return default


def _open_events(session: Session, journey: Journey) -> list[Event]:
    return list(
        session.scalars(
            select(Event)
            .where(
                Event.journey_id == journey.id,
                Event.event_type == EVENT_TYPE,
                Event.provider_key == PROVIDER_KEY,
                Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
            )
            .order_by(Event.detected_at.desc())
        ).all()
    )


def active_recovery_event(session: Session, journey: Journey) -> Event | None:
    rows = _open_events(session, journey)
    return rows[0] if rows else None

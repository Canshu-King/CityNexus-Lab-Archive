"""Durable mid-trip HARD capability recovery.

A newly confirmed HARD capability on an ACTIVE journey invalidates the active
plan.  The consequence must be *durable state*, not a JSON field buried in one
response:

    new HARD capability invalidates active plan
      -> durable Event + recovery state on the Journey
      -> C4 commitments preserved
      -> governed ReplanProposal, or an explicit no-alternative state
      -> visible frontend recovery action

The active plan is never silently rewritten; the traveller must accept a
proposal (or explicitly acknowledge that none exists).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event, Journey, JourneyOutcomeEvent, PlanVersion

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


def open_recovery_event(
    session: Session,
    journey: Journey,
    *,
    capability_code: str,
    capability_params: dict[str, Any] | None = None,
    failures: list[str] | None = None,
) -> Event:
    """Create (or refresh) the durable recovery Event for this Journey."""

    existing = session.scalar(
        select(Event)
        .where(
            Event.journey_id == journey.id,
            Event.event_type == EVENT_TYPE,
            Event.provider_key == PROVIDER_KEY,
            Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
        )
        .order_by(Event.detected_at.desc())
    )
    payload = {
        "capability_code": capability_code,
        "capability_params": dict(capability_params or {}),
        "active_plan_version_id": journey.active_plan_version_id,
        "feasibility_failures": list(failures or []),
        "requires_user_decision": True,
        "silent_plan_mutation": False,
    }
    now = _now()
    if existing is not None:
        existing.payload_json = _json(payload)
        existing.detected_at = now
        existing.status = "DETECTED"
        return existing
    event = Event(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key=PROVIDER_KEY,
        provenance="USER_REPORTED",
        event_type=EVENT_TYPE,
        severity="MAJOR",
        status="DETECTED",
        affected_activity_id=None,
        occurred_at=now,
        detected_at=now,
        resolved_at=None,
        payload_json=_json(payload),
        created_at=now,
    )
    session.add(event)
    session.flush()
    return event


def resolve_recovery_events(session: Session, journey: Journey) -> int:
    """Mark every open recovery Event resolved (plan is feasible again)."""

    rows = session.scalars(
        select(Event).where(
            Event.journey_id == journey.id,
            Event.event_type == EVENT_TYPE,
            Event.provider_key == PROVIDER_KEY,
            Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
        )
    ).all()
    now = _now()
    for row in rows:
        row.status = "RESOLVED"
        row.resolved_at = now
    return len(rows)


def active_recovery_event(session: Session, journey: Journey) -> Event | None:
    return session.scalar(
        select(Event)
        .where(
            Event.journey_id == journey.id,
            Event.event_type == EVENT_TYPE,
            Event.provider_key == PROVIDER_KEY,
            Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
        )
        .order_by(Event.detected_at.desc())
    )


def recovery_state(
    session: Session,
    journey: Journey,
    *,
    is_feasible: bool | None = None,
    failures: list[str] | None = None,
) -> dict[str, Any] | None:
    """Project the durable recovery facts for the phone UI."""

    event = active_recovery_event(session, journey)
    if event is None:
        return None
    payload = _load(event.payload_json, {})
    proposals = session.scalars(
        select(PlanVersion).where(
            PlanVersion.journey_id == journey.id,
            PlanVersion.status == "CANDIDATE",
        )
    ).all()
    state = ACTIVE if is_feasible is False else NO_ALTERNATIVE if is_feasible is None else RESOLVED
    return {
        "state": state,
        "kind": RECOVERY_KIND,
        "event_id": event.id,
        "event_status": event.status,
        "capability_code": payload.get("capability_code"),
        "active_plan_version_id": journey.active_plan_version_id,
        "failures": list(failures or payload.get("feasibility_failures") or []),
        "candidate_plan_count": len(proposals),
        "candidate_plan_ids": [item.id for item in proposals],
        "requires_user_decision": True,
        "silent_plan_mutation": False,
        "actions": ["REPLAN", "ACKNOWLEDGE_NO_ALTERNATIVE"],
        "detected_at": event.detected_at,
    }


def recovery_flags(session: Session, journey: Journey) -> dict[str, Any]:
    """Compact booleans for `/experience` clients."""

    event = active_recovery_event(session, journey)
    if event is None:
        return {"needs_review": False, "recovery_required": False}
    payload = _load(event.payload_json, {})
    return {
        "needs_review": True,
        "recovery_required": True,
        "recovery_event_id": event.id,
        "recovery_capability_code": payload.get("capability_code"),
        "recovery_state": ACTIVE,
    }

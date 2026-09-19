from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.gateway import AgentToolGateway
from app.agent.mission import mission_payload
from app.core.audit import record_audit
from app.db.models import (
    AgentRun,
    AgentRunStep,
    Event,
    GuardianRun,
    Journey,
    JourneyMission,
    ReplanProposal,
)
from app.schemas import AgentToolCall

ACTIONABLE_EVENT_TYPES = frozenset({"WEATHER", "CLOSURE", "TRAFFIC_DELAY", "SCHEDULE_DELAY"})
SEVERITY_ORDER = {"CRITICAL": 4, "MAJOR": 3, "MINOR": 2, "INFO": 1}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _standing_mission(session: Session, journey_id: str) -> JourneyMission | None:
    return session.scalar(
        select(JourneyMission)
        .where(
            JourneyMission.journey_id == journey_id,
            JourneyMission.is_standing.is_(True),
            JourneyMission.status == "ACTIVE",
        )
        .order_by(JourneyMission.created_at.desc(), JourneyMission.id.desc())
    )


def _open_events(session: Session, journey_id: str) -> list[Event]:
    return list(
        session.scalars(
            select(Event)
            .where(Event.journey_id == journey_id, Event.status.in_(("DETECTED", "ACKNOWLEDGED")))
            .order_by(Event.detected_at, Event.id)
        ).all()
    )


def _fingerprint(journey: Journey, mission: JourneyMission | None, events: list[Event]) -> str:
    material = {
        "journey_id": journey.id,
        "active_plan_version_id": journey.active_plan_version_id,
        "mission_id": mission.id if mission else None,
        "mission_resolved_intent": mission.resolved_intent_json if mission else None,
        "events": [
            {
                "id": event.id,
                "type": event.event_type,
                "severity": event.severity,
                "status": event.status,
                "affected_activity_id": event.affected_activity_id,
                "payload": event.payload_json,
            }
            for event in events
        ],
    }
    return hashlib.sha256(_json(material).encode("utf-8")).hexdigest()


def guardian_payload(
    session: Session, run: GuardianRun, *, deduplicated: bool = False
) -> dict[str, Any]:
    mission = (
        session.get(JourneyMission, run.standing_mission_id) if run.standing_mission_id else None
    )
    agent = session.get(AgentRun, run.agent_run_id) if run.agent_run_id else None
    steps = []
    if agent is not None:
        rows = session.scalars(
            select(AgentRunStep)
            .where(AgentRunStep.run_id == agent.id)
            .order_by(AgentRunStep.sequence_no)
        ).all()
        steps = [
            {
                "sequence_no": row.sequence_no,
                "tool_name": row.tool_name,
                "arguments": json.loads(row.arguments_json or "{}"),
                "result": json.loads(row.result_json or "{}"),
                "decision": row.decision,
                "status": row.status,
            }
            for row in rows
        ]
    return {
        "id": run.id,
        "journey_id": run.journey_id,
        "decision": run.decision,
        "status": run.status,
        "action_status": run.action_status,
        "deduplicated": deduplicated,
        "standing_mission": mission_payload(mission) if mission else None,
        "trigger_event_id": run.trigger_event_id,
        "proposal_id": run.proposal_id,
        "agent_run_id": run.agent_run_id,
        "agent_runtime": (
            {
                "provider_key": agent.provider_key,
                "model_key": agent.model_key,
                "status": agent.status,
            }
            if agent
            else None
        ),
        "tool_steps": steps,
        "evidence": json.loads(run.evidence_json or "{}"),
        "reasoning_summary": run.reasoning_summary,
        "active_plan_before_id": run.active_plan_before_id,
        "active_plan_after_id": run.active_plan_after_id,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "cooldown_until": run.cooldown_until,
    }


def _new_agent_run(session: Session, journey: Journey, mission: JourneyMission) -> AgentRun:
    now = _now().isoformat()
    run = AgentRun(
        id=str(uuid4()),
        mission_id=mission.id,
        journey_id=journey.id,
        provider_key="citynexus-guardian",
        model_key="deterministic-recovery-controller-v1",
        status="RUNNING",
        created_at=now,
        started_at=now,
    )
    session.add(run)
    session.flush()
    return run


def _step(
    session: Session,
    run: AgentRun,
    sequence: int,
    tool: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> None:
    now = _now().isoformat()
    session.add(
        AgentRunStep(
            id=str(uuid4()),
            run_id=run.id,
            sequence_no=sequence,
            tool_name=tool,
            arguments_json=_json(arguments),
            result_json=_json(result),
            decision=result.get("decision"),
            status="COMPLETED",
            created_at=now,
            completed_at=now,
        )
    )


def scan_guardian(session: Session, journey: Journey) -> dict[str, Any]:
    """Observe persisted journey facts and launch at most one recovery per incident state."""

    mission = _standing_mission(session, journey.id)
    events = _open_events(session, journey.id)
    actionable_events = [event for event in events if event.event_type in ACTIONABLE_EVENT_TYPES]
    if actionable_events:
        handled = list(
            session.scalars(
                select(GuardianRun)
                .where(
                    GuardianRun.journey_id == journey.id,
                    GuardianRun.trigger_event_id.in_([event.id for event in actionable_events]),
                    GuardianRun.status == "COMPLETED",
                )
                .order_by(GuardianRun.created_at.desc())
            ).all()
        )
        handled_ids = {item.trigger_event_id for item in handled}
        for item in handled:
            try:
                prior_evidence = json.loads(item.evidence_json or "{}")
                handled_ids.update(
                    prior_evidence.get("observation", {}).get("actionable_event_ids", [])
                )
            except (json.JSONDecodeError, AttributeError):
                continue
        actionable_events = [event for event in actionable_events if event.id not in handled_ids]
        if not actionable_events and handled:
            return guardian_payload(session, handled[0], deduplicated=True)
    fingerprint = _fingerprint(journey, mission, events)
    existing = session.scalar(
        select(GuardianRun).where(
            GuardianRun.journey_id == journey.id,
            GuardianRun.evidence_fingerprint == fingerprint,
        )
    )
    if existing is not None:
        return guardian_payload(session, existing, deduplicated=True)

    now = _now()
    actionable = actionable_events
    evidence = {
        "observation": {
            "journey_status": journey.status,
            "active_plan_version_id": journey.active_plan_version_id,
            "open_event_ids": [event.id for event in events],
            "actionable_event_ids": [event.id for event in actionable],
        },
        "inference": {},
        "solver": None,
        "policy": None,
        "mutation": None,
    }
    if not actionable:
        decision, action_status = "NO_ACTION", "NO_ACTION"
        summary = (
            "No unresolved weather, closure, traffic, or schedule disruption requires recovery."
        )
    elif mission is None:
        decision, action_status = "WATCH", "MISSION_REQUIRED"
        summary = "A disruption is present, but no standing Journey mission defines the autonomy envelope."
    else:
        decision, action_status = "RECOVERY_REQUIRED", "PLANNING"
        summary = "Guardian found an actionable disruption and launched one bounded recovery run."

    run = GuardianRun(
        id=str(uuid4()),
        journey_id=journey.id,
        standing_mission_id=mission.id if mission else None,
        trigger_event_id=None,
        agent_run_id=None,
        proposal_id=None,
        decision=decision,
        status="RUNNING" if decision == "RECOVERY_REQUIRED" else "COMPLETED",
        action_status=action_status,
        evidence_fingerprint=fingerprint,
        evidence_json=_json(evidence),
        reasoning_summary=summary,
        active_plan_before_id=journey.active_plan_version_id,
        active_plan_after_id=journey.active_plan_version_id,
        created_at=now.isoformat(),
        completed_at=None if decision == "RECOVERY_REQUIRED" else now.isoformat(),
        cooldown_until=(now + timedelta(minutes=15)).isoformat(),
    )
    session.add(run)
    session.flush()
    if decision != "RECOVERY_REQUIRED":
        session.commit()
        return guardian_payload(session, run)

    trigger = max(
        actionable,
        key=lambda item: (SEVERITY_ORDER.get(item.severity, 0), item.detected_at, item.id),
    )
    run.trigger_event_id = trigger.id
    evidence["inference"] = {
        "decision": "RECOVERY_REQUIRED",
        "selected_trigger_event_id": trigger.id,
        "reason": "highest-severity actionable unresolved event",
    }
    agent = _new_agent_run(session, journey, mission)
    run.agent_run_id = agent.id
    session.commit()
    gateway = AgentToolGateway(session)
    inspect_args = {
        "request_id": f"guardian-inspect-{run.id}",
        "agent_id": "guardian",
        "journey_id": UUID(journey.id),
        "mission_id": UUID(mission.id),
    }
    inspect = gateway.dispatch("inspect_twin", AgentToolCall(**inspect_args))
    _step(session, agent, 1, "inspect_twin", inspect_args, inspect)
    request_args = {
        "request_id": f"guardian-replan-{run.id}",
        "agent_id": "guardian",
        "journey_id": UUID(journey.id),
        "mission_id": UUID(mission.id),
        "trigger_event_id": UUID(trigger.id),
        "candidate_count": 3,
        "solver_mode": "v2",
    }
    try:
        generated = gateway.dispatch("request_replan", AgentToolCall(**request_args))
    except HTTPException as exc:
        generated = {"decision": "DENY", "error": str(exc.detail), "executed": False}
        _step(session, agent, 2, "request_replan", request_args, generated)
        run.action_status = "NO_FEASIBLE_RECOVERY"
        run.reasoning_summary = (
            f"Recovery was required, but no feasible proposal was produced: {exc.detail}"
        )
        agent.status = "COMPLETED"
        agent.outcome = run.reasoning_summary
        agent.completed_at = _now().isoformat()
        run.status = "COMPLETED"
        run.completed_at = agent.completed_at
        run.evidence_json = _json(evidence)
        session.commit()
        return guardian_payload(session, run)
    _step(session, agent, 2, "request_replan", request_args, generated)
    proposal_id = str(generated["proposal"]["id"])
    proposal = session.get(ReplanProposal, proposal_id)
    run.proposal_id = proposal_id
    diff = json.loads(proposal.diff_json or "{}") if proposal else {}
    evidence["solver"] = diff.get("verified_evidence", {}).get("generator")
    resolved = json.loads(mission.resolved_intent_json or "{}")
    mission_cost_limit = int(resolved.get("max_cost_delta_minor", 0))
    mission_drift_limit = int(resolved.get("max_schedule_drift_min", 0))
    cost_delta = max(0, int(diff.get("cost_delta_minor") or 0))
    drift = abs(int(diff.get("end_time_delta_min") or 0))
    envelope_allows = (
        mission.requested_autonomy == "EXECUTE_WITHIN_BOUNDS"
        and cost_delta <= mission_cost_limit
        and drift <= mission_drift_limit
    )
    if envelope_allows:
        accept_args = {
            "request_id": f"guardian-accept-{run.id}",
            "agent_id": "guardian",
            "journey_id": UUID(journey.id),
            "mission_id": UUID(mission.id),
            "proposal_id": UUID(proposal_id),
        }
        accepted = gateway.dispatch("accept_replan", AgentToolCall(**accept_args))
        _step(session, agent, 3, "accept_replan", accept_args, accepted)
        evidence["policy"] = {
            "decision": accepted.get("decision"),
            "reason_codes": accepted.get("reason_codes", []),
            "policy_version": accepted.get("policy_version"),
        }
        evidence["mutation"] = {
            "executed": bool(accepted.get("executed")),
            "proposal_id": proposal_id,
        }
        run.action_status = (
            "EXECUTED"
            if accepted.get("executed")
            else accepted.get("decision", "REQUIRE_CONFIRMATION")
        )
    else:
        reason_codes = []
        if mission.requested_autonomy != "EXECUTE_WITHIN_BOUNDS":
            reason_codes.append("MISSION_PLAN_ONLY")
        if cost_delta > mission_cost_limit:
            reason_codes.append("MISSION_COST_LIMIT_EXCEEDED")
        if drift > mission_drift_limit:
            reason_codes.append("MISSION_SCHEDULE_DRIFT_EXCEEDED")
        evidence["policy"] = {"decision": "REQUIRE_CONFIRMATION", "reason_codes": reason_codes}
        evidence["mutation"] = {"executed": False, "proposal_id": proposal_id}
        run.action_status = "REQUIRE_CONFIRMATION"

    session.refresh(journey)
    completed = _now().isoformat()
    run.active_plan_after_id = journey.active_plan_version_id
    run.evidence_json = _json(evidence)
    run.status = "COMPLETED"
    run.completed_at = completed
    agent.status = "COMPLETED"
    agent.outcome = run.action_status
    agent.completed_at = completed
    record_audit(
        session,
        action="guardian.scan.completed",
        entity_type="GuardianRun",
        entity_id=run.id,
        journey_id=journey.id,
        actor_type="AI_AGENT",
        actor_id="guardian",
        after={
            "decision": run.decision,
            "action_status": run.action_status,
            "proposal_id": proposal_id,
        },
    )
    session.commit()
    return guardian_payload(session, run)


def guardian_status(session: Session, journey: Journey) -> dict[str, Any]:
    mission = _standing_mission(session, journey.id)
    runs = list(
        session.scalars(
            select(GuardianRun)
            .where(GuardianRun.journey_id == journey.id)
            .order_by(GuardianRun.created_at.desc(), GuardianRun.id.desc())
            .limit(20)
        ).all()
    )
    return {
        "journey_id": journey.id,
        "standing_mission": mission_payload(mission) if mission else None,
        "current_active_plan_version_id": journey.active_plan_version_id,
        "latest": guardian_payload(session, runs[0]) if runs else None,
        "runs": [guardian_payload(session, item) for item in runs],
    }

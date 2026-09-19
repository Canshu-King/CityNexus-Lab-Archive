

def recovery_state(
    session: Session,
    journey: Journey,
    *,
    is_feasible: bool | None = None,
    failures: list[str] | None = None,
) -> dict[str, Any] | None:
    """Project the durable recovery facts for the phone UI.

    The projected state is derived from persisted facts, never from a caller's
    ``is_feasible`` argument alone:

    * a recorded replan attempt with zero feasible candidates -> NO_ALTERNATIVE
    * an acknowledgement does not change the state, only the event status
    * an open event whose plan is feasible again -> RESOLVED projection
    """

    event = active_recovery_event(session, journey)
    if event is None:
        return None
    payload = _load(event.payload_json, {})
    if is_feasible is True:
        state = RESOLVED
    elif payload.get("replan_attempted") and payload.get("no_alternative"):
        state = NO_ALTERNATIVE
    else:
        state = ACTIVE
    candidate_ids = [
        str(item)
        for item in (
            payload.get("feasible_candidate_ids")
            or [
                row.id
                for row in session.scalars(
                    select(PlanVersion).where(
                        PlanVersion.journey_id == journey.id,
                        PlanVersion.status == "CANDIDATE",
                    )
                ).all()
            ]
        )
    ]
    return {
        "state": state,
        "kind": RECOVERY_KIND,
        "event_id": event.id,
        "event_status": event.status,
        "acknowledged": event.status == ACKNOWLEDGED,
        "acknowledged_at": payload.get("acknowledged_at"),
        "capability_code": payload.get("capability_code"),
        "active_plan_version_id": journey.active_plan_version_id,
        "failures": list(failures or payload.get("feasibility_failures") or []),
        "replan_attempted": bool(payload.get("replan_attempted")),
        "no_alternative": bool(payload.get("no_alternative")),
        "candidate_plan_count": len(candidate_ids),
        "candidate_plan_ids": candidate_ids,
        "requires_user_decision": True,
        "silent_plan_mutation": False,
        "actions": ["REPLAN", "ACKNOWLEDGE_WARNING"],
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
        "acknowledged": event.status == ACKNOWLEDGED,
        "recovery_event_id": event.id,
        "recovery_capability_code": payload.get("capability_code"),
        "recovery_state": (
            NO_ALTERNATIVE
            if payload.get("replan_attempted") and payload.get("no_alternative")
            else ACTIVE
        ),
    }
